import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from db.session import async_session_maker
from crud.course_crud.learning_status_crud import learning_status_crud
from services.auth_client import auth_client

logger = logging.getLogger(__name__)


async def update_single_user(user_id: int, db: AsyncSession, admin_cookie: str = None) -> bool:
    try:
        has_completed_all = await learning_status_crud.check_user_completed_all_courses(db, user_id)
        
        if has_completed_all:
            # Передаем admin_cookie в метод получения статуса
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


async def bulk_update_all_users(admin_cookie: str = None):
    db = async_session_maker()
    try:
        # Передаем admin_cookie в get_all_users
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
                has_completed_all = await learning_status_crud.check_user_completed_all_courses(
                    db, user_id
                )
                
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
            # Обновляем пачками по 50 пользователей
            batch_size = 50
            for i in range(0, len(users_to_update), batch_size):
                batch = users_to_update[i:i + batch_size]
                success = await auth_client.bulk_update_learning_status(batch)
                if success:
                    updated_count += len(batch)
                    logger.info(f"Updated batch of {len(batch)} users")
                else:
                    logger.error(f"Failed to update batch of users")
                
                # Небольшая задержка между батчами
                await asyncio.sleep(0.1)
        else:
            logger.info("No users need status update")

        logger.info(f"Updated {updated_count} users")
        return {"updated": updated_count, "total": len(users), "eligible": len(users_to_update)}

    finally:
        await db.close()


@shared_task(name="services.learning_tasks.update_all_users_learning_status")
def update_all_users_learning_status():
    """
    Запланированная задача для обновления статусов.
    Запускается без admin_cookie, поэтому не может получить список пользователей из auth.
    """
    logger.info("Starting scheduled update of learning status")
    logger.warning("Эта задача не сможет получить список пользователей без admin_cookie!")
    
    # Здесь проблема - нет admin_cookie при автоматическом запуске
    # Нужно либо использовать сервис-сервис токен, либо другую ручку
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Без admin_cookie это не сработает!
        result = loop.run_until_complete(bulk_update_all_users(admin_cookie=None))
        logger.info(f"Completed: {result}")
        return result
    finally:
        loop.close()
