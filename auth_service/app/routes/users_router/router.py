import json
import aio_pika
from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
    Depends,
    BackgroundTasks,
)
from sqlalchemy import select
from schemas.user_schemas.user_register import UserRegister
from schemas.user_schemas.user_password import ChangePasswordSchema
from schemas.user_schemas.user_auth import UserAuth
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from services.jwt import create_access_token
from services.emailsender import send_confirmation_email
import asyncio
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from services.rabbitmq import get_rabbitmq_connection
from aio_pika.abc import AbstractRobustConnection
from services.yandex_oauth import yandex_router
from services.vk_oauth import vk_router
import time


router = APIRouter(prefix="/users_interaction")

auth_router = APIRouter(tags=["Authentication"])
email_router = APIRouter(tags=["Email Management"])
user_management_router = APIRouter(tags=["User Management"])


# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С МЕТРИКАМИ ====================
def _get_metric_active_users():
    """Получает метрику active_users_total (lazy import для избежания циклической зависимости)"""
    try:
        from main import ACTIVE_USERS

        return ACTIVE_USERS
    except ImportError as e:
        print(f"Warning: Could not import ACTIVE_USERS: {e}")
        return None


def _get_service_name():
    """Получает название сервиса"""
    try:
        from main import SERVICE_NAME

        return SERVICE_NAME
    except ImportError:
        return "auth_service"


def update_active_users_metric(active_count: int):
    """Обновляет метрику активных пользователей"""
    metric = _get_metric_active_users()
    service_name = _get_service_name()

    if metric and service_name:
        try:
            metric.labels(service=service_name).set(active_count)
            print(
                f"✓ Metric updated: active_users_total{{{service_name}}} = {active_count}"
            )
        except Exception as e:
            print(f"✗ Error updating metric: {e}")
    else:
        print(f"⚠ Could not update metric: metric={metric}, service={service_name}")


# ========================================================================


@auth_router.post("/register/")
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection),
    background_tasks: BackgroundTasks = None,
):
    try:
        user, confirmation_token, temp_login = await UserCRUD.create_user(db, user_data)

        if background_tasks:
            background_tasks.add_task(
                send_confirmation_email, user.email, confirmation_token, temp_login
            )
        else:
            asyncio.create_task(
                send_confirmation_email(user.email, confirmation_token, temp_login)
            )

        try:
            channel = await rabbitmq.channel()
            exchange = await channel.declare_exchange(
                "user_events", type="direct", durable=True
            )

            user_data_message = {
                "user_id": user.id,
                "email": user.email,
                "username": temp_login,
                "name": user.temp_name,
                "verified": False,
                "event_type": "user_registered",
                "role": user.role.value,
            }

            message = aio_pika.Message(
                body=json.dumps(user_data_message).encode(),
                headers={"event_type": "user_events"},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(message, routing_key="user.created")

        except Exception as e:
            print(f"Failed to send RabbitMQ message: {e}")

        return {
            "message": "User registered successfully. Please check your email for verification.",
            "user_id": user.id,
            "email": user.email,
            "future_login": temp_login,
            "role": user.role,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@auth_router.post("/login/")
async def auth_user(
    response: Response, user_data: UserAuth, db: AsyncSession = Depends(get_db)
):
    password_str = user_data.password.get_secret_value()
    user = await User.check_user(login=user_data.login, password=password_str, db=db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login/email or password",
        )

    access_token = await create_access_token(
        {"sub": str(user["id"]), "role": user["role"]}
    )
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)

    return "Access successed"


@auth_router.post("/logout/")
async def logout_user():
    response = JSONResponse(content={"message": "Successfully logged out"})
    
    
    response.delete_cookie(
        key="users_access_token",
        path="/",
        domain=".rosdk.ru",  
        secure=True,
        httponly=True,
        samesite="none"  
    )
    
    
    response.delete_cookie(
        key="userData",
        path="/",
        domain=".rosdk.ru",  
        secure=True,
        samesite="none"
    )
    
    return response


@email_router.get("/confirm-email")
async def confirm_email(
    token: str,
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection),
):
    user = await UserCRUD.confirm_user_email(db, token)

    try:
        channel = await rabbitmq.channel()
        exchange = await channel.declare_exchange(
            "user_events", type="direct", durable=True
        )
        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)

        user_data_message = {
            "user_id": user.id,
            "email": user.email,
            "username": user.login,
            "name": user.name,
            "is_verified": True,
            "event_type": "user_verified",
            "role": user.role.value,
        }

        message = aio_pika.Message(
            body=json.dumps(user_data_message).encode(),
            headers={"event_type": "user_verified"},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key="user.verified")
    except Exception as e:
        print(f"Failed to send RabbitMQ message: {e}")

    current_dir = Path(__file__).parent
    html_file_path = current_dir / "mailsend.html"
    if html_file_path.exists():
        html_content = html_file_path.read_text(encoding="utf-8")
        html_content = html_content.replace("{User_NAME}", user.name)
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(content="<h1>confirmed</h1>", status_code=200)


@email_router.post("/resend-confirmation/")
async def resend_confirmation(
    email: str,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    import uuid

    new_token = str(uuid.uuid4())
    user.confirmation_token = new_token
    await db.commit()

    if background_tasks:
        background_tasks.add_task(send_confirmation_email, user.email, new_token)
    else:
        await send_confirmation_email(user.email, new_token)

    return {"message": "Confirmation email sent successfully"}


@user_management_router.get("/get_users/", description="Для админа будет токен")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    try:
        users = await UserCRUD.get_all_users(db)

        print(f"\n{'=' * 60}")
        print(f"DEBUG get_all_users:")
        print(f"  Всего пользователей: {len(users)}")

        if users:
            print(f"  Первый пользователь: {users[0]}")
            print(f"  Поле 'verified': {users[0].get('verified')}")

       
        active_count = 0
        for user in users:
            if user.get("verified", False):
                active_count += 1

        print(f"  Активных пользователей: {active_count}")
        print(f"{'=' * 60}\n")

        
        update_active_users_metric(active_count)

        return users
    except Exception as e:
        print(f"ERROR in get_all_users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@user_management_router.delete("/delete_user/")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await UserCRUD.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@user_management_router.patch("/change_password/")
async def change_password(
    user_id: int, passwords: ChangePasswordSchema, db: AsyncSession = Depends(get_db)
):
    try:
        await UserCRUD.change_user_password(
            db=db,
            user_id=user_id,
            old_password=passwords.current_password.get_secret_value(),
            new_password=passwords.new_password.get_secret_value(),
        )
        return {"message": "Password changed success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error is in {str(e)}")


@user_management_router.get("/get_user_by_id/{user_id}")
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await UserCRUD.get_user_by_id(db=db, user_id=user_id)
        return user
    except Exception:
        raise HTTPException(status_code=404, detail=f"user with id {user_id} not found")


# ==================== ТЕСТОВЫЕ ЭНДПОИНТЫ ДЛЯ ПРОВЕРКИ ====================
@router.get("/test-metric")
async def test_metric():
    """Тестовый эндпоинт для проверки работы метрик"""
    try:
        # Устанавливаем тестовое значение
        update_active_users_metric(777)

        # Проверяем текущее значение
        metric = _get_metric_active_users()
        service_name = _get_service_name()

        return {
            "message": "Test metric endpoint",
            "metric": "active_users_total",
            "service": service_name,
            "test_value": 777,
            "metric_object": str(metric) if metric else "Not found",
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": time.time(),
        "endpoints": {
            "metrics": "/auth/metrics",
            "test_metric": "/auth/users_interaction/test-metric",
            "get_users": "/auth/users_interaction/get_users",
        },
    }


# ========================================================================


# Подключаем все роутеры
router.include_router(auth_router)
router.include_router(email_router)
router.include_router(user_management_router)
router.include_router(yandex_router)
router.include_router(vk_router)


