from db.models.user_progress import UserProgress
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.submission import Submission, SubmissionStatus
from typing import List, Optional
from services.auth_client import auth_client
from services.emailsender import send_ok_email
from services.emailsender import send_bad_email
from services.assignement import assignment_service


class SubmissionCRUD:
    
    async def create_submission(self, db: AsyncSession, user_id: int, course_id: int, file_url: str) -> Submission:
        progress_result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.course_id == course_id
            )
        )
        user_progress = progress_result.scalar_one_or_none()

        existing_submission = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.course_id == course_id,
                Submission.status == SubmissionStatus.PENDING
            )
        )
        existing = existing_submission.scalar_one_or_none()
        if existing:
            raise ValueError("You already have a pending submission for this course")

        if user_progress and user_progress.is_completed:
            raise ValueError("Course is already completed, no new submissions allowed")

        submission = Submission(user_id=user_id, course_id=course_id, file_url=file_url)
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission
    
    async def get_pending_submissions(self, db: AsyncSession) -> List[Submission]:
        result = await db.execute(
            select(Submission).where(Submission.status == SubmissionStatus.PENDING)
        )
        return result.scalars().all()
    
    async def get_pending_submission_ids(self, db: AsyncSession) -> List[int]:

        result = await db.execute(
            select(Submission.id).where(Submission.status == SubmissionStatus.PENDING)
        )
        return [row[0] for row in result.all()]
    
    async def get_submissions_by_ids(self, db: AsyncSession, submission_ids: List[int]) -> List[Submission]:

        if not submission_ids:
            return []
        result = await db.execute(
            select(Submission).where(Submission.id.in_(submission_ids))
        )
        return result.scalars().all()
    
    async def get_submission_by_id(self, db: AsyncSession, submission_id: int) -> Optional[Submission]:
        result = await db.execute(select(Submission).where(Submission.id == submission_id))
        return result.scalar_one_or_none()
    
    async def review_submission(self, db: AsyncSession, submission_id: int, status: SubmissionStatus, description: str) -> Optional[Submission]:
        result = await db.execute(select(Submission).where(Submission.id == submission_id))
        submission = result.scalar_one_or_none()
        
        if not submission:
            return None

        user_email = await auth_client.get_user_email(submission.user_id)

        if not user_email:
            print(f"Could not find email for user {submission.user_id}")
        
        submission.status = status

        if status == SubmissionStatus.APPROVED:
            await self.mark_course_completed(db, submission.user_id, submission.course_id)
            if user_email:
                await send_ok_email(user_email, description)  
        elif status == SubmissionStatus.REJECTED:
            if user_email:
                await send_bad_email(user_email, description)  

        await db.commit()
        await db.refresh(submission)
        

        await assignment_service.remove_assignment(submission_id)
        
        return submission
    
    async def mark_course_completed(self, db: AsyncSession, user_id: int, course_id: int):
        progress_result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.course_id == course_id
            )
        )
        user_progress = progress_result.scalar_one_or_none()
        
        if user_progress:
            user_progress.is_completed = True
        else:
            user_progress = UserProgress(
                user_id=user_id,
                course_id=course_id,
                is_completed=True
            )
            db.add(user_progress)

    async def get_user_submissions(self, db: AsyncSession, user_id: int) -> List[Submission]:
        result = await db.execute(
            select(Submission).where(Submission.user_id == user_id)
        )
        return result.scalars().all()

    async def get_user_submission_by_course(self, db: AsyncSession, user_id: int, course_id: int) -> Optional[Submission]:
        result = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.course_id == course_id
            )
        )
        return result.scalar_one_or_none()


submission_crud = SubmissionCRUD()