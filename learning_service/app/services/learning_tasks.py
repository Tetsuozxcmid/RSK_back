import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
from typing import List, Dict, Optional

from db.session import async_session_maker
from crud.course_crud.learning_status_crud import learning_status_crud
from services.auth_client import auth_client
from services.profile_client import profile_client

logger = logging.getLogger(__name__)

# ========== СТАРЫЕ ФУНКЦИИ (для тестовых ручек) ==========

async def update_single_user(user_id: int, db: AsyncSession, admin_cookie: str = None) -> bool:
    """
    Обновить статус одного пользователя (для тестовых ручек)
    """
    try:
        has_completed_all = await learning_status_crud.check_user_completed_all_courses(db, user_id)
        
        if has_completed_all:
            current_status = await auth_client.get_user_learning_status(user_id, admin_cookie)
            
            if current_status is False:
                logger.info(f"User {user_id} completed all courses, updating to True")
                return await auth_client.update_user_learning_status(user_id, True)
            else:
                logger.debug(f"User {user_id} already has learning={current_status}")
                return True
        else:
            logger.debug(f"User {user_id} hasn't completed all courses yet")
            return True
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False


async def bulk_update_all_users(admin_cookie: str = None) -> Dict:
    """
    Массовое обновление всех пользователей (для тестовых ручек)
    """
    db = async_session_maker()
    try:
        users = await auth_client.get_all_users(admin_cookie=admin_cookie)

        if not users:
            logger.warning("No users found")
            return {"updated": 0, "total": 0}

        # Собираем пользователей, которым нужно обновить статус
        users_to_update = []
        
        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue

            try:
                has_completed_all = await learning_status_crud.check_user_completed_all_courses(db, user_id)
                
                if has_completed_all:
                    current_status = await auth_client.get_user_learning_status(user_id, admin_cookie)
                    if current_status is False:
                        users_to_update.append({
                            "user_id": user_id,
                            "is_learned": True
                        })
            except Exception as e:
                logger.error(f"Error checking user {user_id}: {e}")
                continue

        # Массовое обновление
        updated_count = 0
        if users_to_update:
            batch_size = 50
            for i in range(0, len(users_to_update), batch_size):
                batch = users_to_update[i:i + batch_size]
                success = await auth_client.bulk_update_learning_status(batch)
                if success:
                    updated_count += len(batch)
                    logger.info(f"Updated batch of {len(batch)} users")
                else:
                    logger.error(f"Failed to update batch of users")
                
                await asyncio.sleep(0.1)
        else:
            logger.info("No users need status update")

        logger.info(f"Updated {updated_count} users")
        return {"updated": updated_count, "total": len(users), "eligible": len(users_to_update)}

    finally:
        await db.close()


# ========== НОВЫЕ ФУНКЦИИ (для Celery) ==========

async def find_users_to_update() -> List[Dict]:
    """
    Найти всех пользователей, которые прошли все курсы
    """
    users_to_update = []
    
    # Получаем всех пользователей из auth сервиса
    users = await auth_client.get_all_users_internal()
    
    if not users:
        logger.warning("No users found from auth service")
        return []
    
    logger.info(f"📊 Checking {len(users)} users for learning status update")
    
    async with async_session_maker() as db:
        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue
            
            try:
                # Проверяем, прошел ли пользователь все курсы
                has_completed = await learning_status_crud.check_user_completed_all_courses(db, user_id)
                
                if has_completed:
                    logger.info(f"✅ User {user_id} completed all courses, will update")
                    users_to_update.append({
                        "user_id": user_id,
                        "is_learned": True
                    })
                else:
                    logger.debug(f"⏭️ User {user_id} not completed all courses")
                    
            except Exception as e:
                logger.error(f"❌ Error checking user {user_id}: {e}")
                continue
    
    logger.info(f"🎯 Found {len(users_to_update)} users to update")
    return users_to_update


@shared_task(
    name="services.learning_tasks.update_learning_statuses",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def update_learning_statuses(self):
    """
    Celery задача: проверить всех пользователей и обновить статусы в profile сервисе.
    Запускается каждый час.
    """
    logger.info("="*60)
    logger.info("🚀 Starting update_learning_statuses task")
    start_time = datetime.now()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Находим пользователей для обновления
        users_to_update = loop.run_until_complete(find_users_to_update())
        
        if not users_to_update:
            logger.info("✅ No users need update")
            return {
                "status": "success",
                "message": "No users need update",
                "checked": "all",
                "updated": 0
            }
        
        # Обновляем статусы батчами по 100 пользователей
        batch_size = 100
        total_updated = 0
        total_failed = 0
        
        for i in range(0, len(users_to_update), batch_size):
            batch = users_to_update[i:i + batch_size]
            logger.info(f"📦 Updating batch {i//batch_size + 1}/{(len(users_to_update)-1)//batch_size + 1}")
            
            # Отправляем батч в profile сервис через internal ручку
            result = loop.run_until_complete(
                profile_client.bulk_update_learning_status(batch)
            )
            
            if result.get("status") == "success":
                updated = result.get("updated", 0)
                total_updated += updated
                if updated < len(batch):
                    logger.warning(f"⚠️ Batch partially updated: {updated}/{len(batch)}")
                else:
                    logger.info(f"✅ Batch fully updated: {updated} users")
            else:
                total_failed += len(batch)
                logger.error(f"❌ Batch completely failed: {result}")
            
            # Небольшая задержка между батчами
            loop.run_until_complete(asyncio.sleep(1))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Task completed in {duration:.2f} seconds")
        logger.info(f"📊 Total updated: {total_updated}/{len(users_to_update)} (failed: {total_failed})")
        
        return {
            "status": "success",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "found_to_update": len(users_to_update),
            "total_updated": total_updated,
            "total_failed": total_failed
        }
        
    except Exception as e:
        logger.error(f"❌ Task failed: {e}", exc_info=True)
        self.retry(exc=e)
        raise
    finally:
        loop.close()