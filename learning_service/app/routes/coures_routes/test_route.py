from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from db.session import async_session_maker
from services.learning_tasks import bulk_update_all_users, update_single_user
from services.auth_client import auth_client, get_admin
from crud.course_crud.learning_status_crud import learning_status_crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test-learning", tags=["Test Learning"])

@router.post("/run-update")
async def run_manual_update(
    background_tasks: BackgroundTasks,
    request: Request,  # Добавляем request
    user_id: Optional[int] = None,
    _: str = Depends(get_admin)  # Проверяем что админ
):
    """
    Ручной запуск обновления статусов обучения.
    """
    try:
        # Получаем токен из куков запроса
        admin_cookie = request.cookies.get("users_access_token")
        
        if user_id:
            # Проверяем существование пользователя
            user = await auth_client.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            
            # Запускаем в фоне
            background_tasks.add_task(run_single_user_update, user_id, admin_cookie)
            
            return {
                "status": "started",
                "message": f"Update started for user {user_id}",
                "user_id": user_id
            }
        else:
            # Запускаем массовое обновление с куками админа
            background_tasks.add_task(run_bulk_update, admin_cookie)
            
            return {
                "status": "started",
                "message": "Bulk update started for all users"
            }
            
    except Exception as e:
        logger.error(f"Error starting manual update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_bulk_update(admin_cookie: str = None):
    logger.info("Running manual bulk update with admin cookie")
    
    # Временно заменяем метод get_all_users в auth_client
    original_get_all_users = auth_client.get_all_users
    
    try:
        # Создаем временную версию метода с куками
        async def get_all_users_with_cookie():
            return await original_get_all_users(admin_cookie=admin_cookie)
        
        # Подменяем метод
        auth_client.get_all_users = get_all_users_with_cookie
        
        # Запускаем обновление
        result = await bulk_update_all_users()
        logger.info(f"Manual bulk update completed: {result}")
    finally:
        # Возвращаем оригинальный метод
        auth_client.get_all_users = original_get_all_users

async def run_single_user_update(user_id: int):
    """Фоновая задача для обновления одного пользователя"""
    logger.info(f"Running manual update for user {user_id}")
    async with async_session_maker() as db:
        result = await update_single_user(user_id, db)
    logger.info(f"Manual update for user {user_id} completed: {result}")

async def run_bulk_update():
    """Фоновая задача для массового обновления"""
    logger.info("Running manual bulk update")
    result = await bulk_update_all_users()
    logger.info(f"Manual bulk update completed: {result}")

@router.get("/check-user/{user_id}")
async def check_user_status(
    user_id: int,
    _: str = Depends(get_admin)  # Только для админов
):
    """
    Проверить статус обучения конкретного пользователя
    """
    try:
        # Проверяем в БД обучения
        async with async_session_maker() as db:
            has_completed = await learning_status_crud.check_user_completed_all_courses(
                db, user_id
            )
        
        # Проверяем в сервисе профилей
        profile_status = await auth_client.get_user_learning_status(user_id)
        
        # Получаем информацию о пользователе
        user_info = await auth_client.get_user_by_id(user_id)
        
        return {
            "user_id": user_id,
            "user_email": user_info.get("email") if user_info else None,
            "has_completed_all_courses": has_completed,
            "current_profile_status": profile_status,
            "needs_update": has_completed and profile_status is False,
            "user_exists_in_auth": user_info is not None
        }
        
    except Exception as e:
        logger.error(f"Error checking user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_learning_stats(
    _: str = Depends(get_admin)  # Только для админов
):
    """
    Получить статистику по обучению пользователей
    """
    try:
        # Получаем всех пользователей
        users = await auth_client.get_all_users()
        
        if not users:
            return {"total_users": 0, "message": "No users found"}
        
        stats = {
            "total_users": len(users),
            "completed_all_courses": 0,
            "already_marked_as_learned": 0,
            "needs_update": 0,
            "not_completed": 0
        }
        
        async with async_session_maker() as db:
            for user in users:
                user_id = user.get("id")
                if not user_id:
                    continue
                
                try:
                    has_completed = await learning_status_crud.check_user_completed_all_courses(
                        db, user_id
                    )
                    
                    if has_completed:
                        stats["completed_all_courses"] += 1
                        
                        # Проверяем статус в профиле
                        profile_status = await auth_client.get_user_learning_status(user_id)
                        if profile_status is True:
                            stats["already_marked_as_learned"] += 1
                        else:
                            stats["needs_update"] += 1
                    else:
                        stats["not_completed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing user {user_id}: {e}")
                    continue
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force-update-user/{user_id}")
async def force_update_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    _: str = Depends(get_admin)
):
    """
    Принудительно обновить статус пользователя (даже если он уже True)
    """
    background_tasks.add_task(force_single_user_update, user_id)
    
    return {
        "status": "started",
        "message": f"Forced update started for user {user_id}"
    }

async def force_single_user_update(user_id: int):
    """Принудительное обновление статуса"""
    logger.info(f"Running forced update for user {user_id}")
    
    async with async_session_maker() as db:
        has_completed = await learning_status_crud.check_user_completed_all_courses(
            db, user_id
        )
        
        if has_completed:
            # Принудительно устанавливаем True
            success = await auth_client.update_user_learning_status(user_id, True)
            logger.info(f"Forced update for user {user_id}: {success}")
        else:
            logger.info(f"User {user_id} hasn't completed all courses, skipping")