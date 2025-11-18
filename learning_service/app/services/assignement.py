import redis.asyncio as aioredis
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from db.models.submission import SubmissionStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models.submission import Submission
from config import settings
import asyncio

class SubmissionAssignmentService:
    def __init__(self, redis_url: str = None):
        self.redis_url = settings.REDIS_URL
        self.redis_client = None
        self.assignment_ttl = 600  
        self.assignment_size = 10  
        self.assignment_prefix = "moderator_assignment:"
        self.submission_lock_prefix = "submission_lock:"
    
    async def connect(self):

        self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):

        if self.redis_client:
            await self.redis_client.aclose()
    
    async def assign_submissions_to_moderator(
        self, 
        db: AsyncSession, 
        moderator_id: int
    ) -> List[int]:

        try:

            available_submissions = await self._get_available_submission_ids(db)
            

            available_submissions = available_submissions[:self.assignment_size]
            

            assigned_ids = []
            for submission_id in available_submissions:
                assignment_key = f"{self.assignment_prefix}{submission_id}"
                lock_key = f"{self.submission_lock_prefix}{submission_id}"
                

                if not await self.redis_client.exists(lock_key):

                    await self.redis_client.setex(
                        assignment_key,
                        self.assignment_ttl,
                        json.dumps({
                            'moderator_id': moderator_id,
                            'assigned_at': time.time(),
                            'expires_at': time.time() + self.assignment_ttl
                        })
                    )

                    await self.redis_client.setex(lock_key, self.assignment_ttl, "locked")
                    assigned_ids.append(submission_id)
            
            return assigned_ids
        except Exception as e:
            print(f"Error assigning submissions to moderator {moderator_id}: {e}")
            return []
    
    async def get_moderator_assignments(self, moderator_id: int) -> List[int]:

        try:

            cursor = 0
            assigned_ids = []
            
            while True:
                cursor, keys = await self.redis_client.scan(cursor=cursor, match=f"{self.assignment_prefix}*")
                for key in keys:
                    assignment_data = await self.redis_client.get(key)
                    if assignment_data:
                        try:
                            data = json.loads(assignment_data)
                            if data.get('moderator_id') == moderator_id:
 
                                if time.time() < data.get('expires_at', 0):
                                    submission_id = key.replace(self.assignment_prefix, "")
                                    assigned_ids.append(int(submission_id))
                                else:

                                    await self.redis_client.delete(key)
                                    await self.redis_client.delete(f"{self.submission_lock_prefix}{submission_id}")
                        except json.JSONDecodeError:
                            continue
                
                if cursor == 0:
                    break
            
            return assigned_ids
        except Exception as e:
            print(f"Error getting moderator assignments for {moderator_id}: {e}")
            return []
    
    async def release_moderator_assignments(self, moderator_id: int):

        try:

            cursor = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(cursor=cursor, match=f"{self.assignment_prefix}*")
                for key in keys:
                    assignment_data = await self.redis_client.get(key)
                    if assignment_data:
                        try:
                            data = json.loads(assignment_data)
                            if data.get('moderator_id') == moderator_id:
                                submission_id = key.replace(self.assignment_prefix, "")
                                await self.redis_client.delete(key)
                                await self.redis_client.delete(f"{self.submission_lock_prefix}{submission_id}")
                        except json.JSONDecodeError:
                            continue
                
                if cursor == 0:
                    break
        except Exception as e:
            print(f"Error releasing moderator assignments for {moderator_id}: {e}")
    
    async def _get_available_submission_ids(self, db: AsyncSession) -> List[int]:

        result = await db.execute(
            select(Submission.id).where(Submission.status == SubmissionStatus.PENDING)
        )
        all_pending_ids = [row[0] for row in result.all()]
        

        available_ids = []
        for sub_id in all_pending_ids:
            assignment_key = f"{self.assignment_prefix}{sub_id}"
            if not await self.redis_client.exists(assignment_key):
                available_ids.append(sub_id)
        
        return available_ids
    
    async def remove_assignment(self, submission_id: int):

        try:
            assignment_key = f"{self.assignment_prefix}{submission_id}"
            lock_key = f"{self.submission_lock_prefix}{submission_id}"
            await self.redis_client.delete(assignment_key)
            await self.redis_client.delete(lock_key)
        except Exception as e:
            print(f"Error removing assignment for submission {submission_id}: {e}")


assignment_service = SubmissionAssignmentService()