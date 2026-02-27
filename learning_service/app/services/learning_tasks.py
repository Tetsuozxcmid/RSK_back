import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from db.session import AsyncSessionLocal
from crud.course_crud.learning_status_crud import learning_status_crud
from services.auth_client import auth_client  

logger = logging.getLogger(__name__)


async def update_single_user(user_id: int, db: AsyncSession) -> bool:
    try:
        completed = await learning_status_crud.check_user_completed_all_courses(db, user_id)
        success = await auth_client.update_user_learning_status(user_id, completed)
        
        if success:
            logger.info(f"User {user_id} learning status updated to {completed}")
        else:
            logger.error(f"Failed to update user {user_id} status in profile service")
        
        return success
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False


async def bulk_update_all_users():
    db = AsyncSessionLocal()
    try:
        users = await auth_client.get_all_users()
        
        if not users:
            logger.warning("No users found")
            return {"updated": 0, "total": 0}
        
        updated = 0
        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue
                
            success = await update_single_user(user_id, db)
            if success:
                updated += 1
            
            await asyncio.sleep(0.5)
        
        logger.info(f"Updated {updated}/{len(users)} users")
        return {"updated": updated, "total": len(users)}
    
    finally:
        await db.close()


@shared_task(name="services.learning_tasks.update_all_users_learning_status")
def update_all_users_learning_status():
    logger.info("Starting scheduled update of learning status")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(bulk_update_all_users())
        logger.info(f"Completed: {result}")
        return result
    finally:
        loop.close()