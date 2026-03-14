import asyncio

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
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
    request: Request,
    user_id: Optional[int] = None,
    _: str = Depends(get_admin)
):
    """
    Ручной запуск обновления статусов обучения.
    """
    try:
        # Получаем токен из куков запроса
        admin_cookie = request.cookies.get("users_access_token")
        logger.info(f"Admin cookie present: {bool(admin_cookie)}")
        
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
            # Запускаем массовое обновление
            background_tasks.add_task(run_bulk_update, admin_cookie)
            
            return {
                "status": "started",
                "message": "Bulk update started for all users"
            }
            
    except Exception as e:
        logger.error(f"Error starting manual update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_single_user_update(user_id: int, admin_cookie: str = None):
    """Фоновая задача для обновления одного пользователя"""
    logger.info(f"Running manual update for user {user_id}")
    async with async_session_maker() as db:
        # Передаем admin_cookie в update_single_user
        result = await update_single_user(user_id, db, admin_cookie)
    logger.info(f"Manual update for user {user_id} completed: {result}")

async def run_bulk_update(admin_cookie: str = None):
    """Фоновая задача для массового обновления"""
    logger.info("Running manual bulk update with admin cookie")
    
    # Передаем admin_cookie в bulk_update_all_users
    result = await bulk_update_all_users(admin_cookie=admin_cookie)
    logger.info(f"Manual bulk update completed: {result}")

@router.get("/check-user/{user_id}")
async def check_user_status(
    user_id: int,
    request: Request,
    _: str = Depends(get_admin)
):
    """
    Проверить статус обучения конкретного пользователя
    """
    try:
        # Получаем куки для возможных запросов
        admin_cookie = request.cookies.get("users_access_token")
        
        # Проверяем в БД обучения
        async with async_session_maker() as db:
            has_completed = await learning_status_crud.check_user_completed_all_courses(
                db, user_id
            )
        
        # Получаем информацию о пользователе
        user_info = await auth_client.get_user_by_id(user_id)
        
        # Получаем статус из профиля
        profile_status = await auth_client.get_user_learning_status(user_id)
        
        return {
            "user_id": user_id,
            "user_email": user_info.get("email") if user_info else None,
            "user_exists": user_info is not None,
            "has_completed_all_courses": has_completed,
            "current_profile_status": profile_status,
            "needs_update": has_completed and profile_status is False
        }
        
    except Exception as e:
        logger.error(f"Error checking user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/sync-update-user/{user_id}")
async def sync_update_user(
    user_id: int,
    request: Request,
    _: str = Depends(get_admin)
):

    try:
        # СНАЧАЛА получаем куки админа из запроса
        admin_cookie = request.cookies.get("users_access_token")
        logger.info(f"🔄 Синхронное обновление пользователя {user_id}")
        logger.info(f"🍪 Admin cookie present: {bool(admin_cookie)}")
        
        # ПОТОМ используем их в запросах
        user = await auth_client.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        async with async_session_maker() as db:
            has_completed = await learning_status_crud.check_user_completed_all_courses(db, user_id)
            logger.info(f"📊 has_completed_all_courses: {has_completed}")
            
            if has_completed:
                # Здесь используем admin_cookie
                current_status = await auth_client.get_user_learning_status(user_id, admin_cookie)
                logger.info(f"📊 current_profile_status: {current_status}")
                
                if current_status is False:
                    update_result = await auth_client.update_user_learning_status(user_id, True)
                    logger.info(f"📤 update_result: {update_result}")
                    
                    new_status = await auth_client.get_user_learning_status(user_id, admin_cookie)
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "has_completed_all_courses": has_completed,
                        "old_status": current_status,
                        "update_result": update_result,
                        "new_status": new_status
                    }
                elif current_status is True:
                    return {
                        "success": True,
                        "user_id": user_id,
                        "message": "User already has learning=True",
                        "current_status": current_status
                    }
                else:
                    return {
                        "success": False,
                        "user_id": user_id,
                        "message": "Could not get current status from profile service",
                        "current_status": current_status,
                        "has_completed_all_courses": has_completed
                    }
            else:
                return {
                    "success": True,
                    "user_id": user_id,
                    "message": "User hasn't completed all courses",
                    "has_completed_all_courses": has_completed
                }
                
    except Exception as e:
        logger.error(f"❌ Error in sync update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/sync-bulk-update")
async def sync_bulk_update(
    request: Request,
    _: str = Depends(get_admin)
):
    """
    Синхронное массовое обновление всех пользователей
    """
    try:
        admin_cookie = request.cookies.get("users_access_token")
        logger.info("🚀 Starting synchronous bulk update")
        
        # Получаем всех пользователей
        users = await auth_client.get_all_users(admin_cookie=admin_cookie)
        logger.info(f"📊 Got {len(users)} users")
        
        results = {
            "total": len(users),
            "checked": 0,
            "updated": 0,
            "errors": 0,
            "details": []
        }
        
        async with async_session_maker() as db:
            for user in users:
                user_id = user.get("id")
                if not user_id:
                    continue
                
                try:
                    logger.info(f"🔍 Checking user {user_id}")
                    
                    # Проверяем, прошел ли все курсы
                    has_completed = await learning_status_crud.check_user_completed_all_courses(db, user_id)
                    
                    if has_completed:
                        # Получаем текущий статус
                        current = await auth_client.get_user_learning_status(user_id, admin_cookie)
                        
                        if current is False:
                            # Обновляем
                            updated = await auth_client.update_user_learning_status(user_id, True)
                            if updated:
                                results["updated"] += 1
                                results["details"].append({
                                    "user_id": user_id,
                                    "status": "updated",
                                    "email": user.get("email")
                                })
                                logger.info(f"✅ Updated user {user_id}")
                            else:
                                results["errors"] += 1
                        else:
                            logger.info(f"⏭️ User {user_id} already learned: {current}")
                    else:
                        logger.info(f"⏭️ User {user_id} not completed all courses")
                    
                    results["checked"] += 1
                    
                    # Небольшая задержка, чтобы не нагружать сервисы
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing user {user_id}: {e}")
                    results["errors"] += 1
                    results["details"].append({
                        "user_id": user_id,
                        "status": "error",
                        "error": str(e)
                    })
        
        logger.info(f"✅ Bulk update completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in sync bulk update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))