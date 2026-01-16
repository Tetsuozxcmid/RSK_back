from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import UserRole
from services.jwt import create_access_token
from services.rabbitmq import get_rabbitmq_connection

from config import settings

import httpx
import aio_pika
import json

vk_router = APIRouter(prefix="/auth/vk", tags=["VK OAuth"])
user_crud = UserCRUD()
COOKIE_NAME = "users_access_token"  

@vk_router.get("/callback")
async def vk_callback(
    request: Request,
    device_id: str | int = None, # type: ignore
    code: str = None, # type: ignore
    error: str = None, # type: ignore
    db: AsyncSession = Depends(get_db),
    rabbitmq: aio_pika.abc.AbstractRobustConnection = Depends(get_rabbitmq_connection)
):
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error={error}")

    code_verifier = request.cookies.get("vkid_sdk:codeVerifier")
    if not code_verifier:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=code_verifier_not_found")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://id.vk.ru/oauth2/auth",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": settings.VK_REDIRECT_URI,
                "client_id": settings.VK_APP_ID,
                "client_secret": settings.VK_APP_SECRET,
                "device_id": device_id
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
       	if not access_token:
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=token_not_received")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://id.vk.ru/oauth2/user_info",
            params={
                "client_id": settings.VK_APP_ID,
                "access_token": access_token
            }
        )
        data = user_resp.json()
        user = data.get("user")

        user_id = user.get("user_id")
        user_first_name = user.get("first_name")
        user_last_name = user.get("last_name")
        user_email = user.get("email")

        user_name = f"{user_first_name} {user_last_name}"

        user = await user_crud.create_oauth_user(
            db=db,
            email=user_email,
            name=user_name,
            provider="vk",
            provider_id=str(user_id),
            role=UserRole.STUDENT
        )
        created = True

        if created:
            try:
                channel = await rabbitmq.channel()
                exchange = await channel.declare_exchange(
                    "user_events",
                    type="direct",
                    durable=True
                )

                user_event = {
                    "user_id": user.id,
                    "email": user.email or user_email or "",
                    "username": user.login or f"vk_user_{user_id}",
                    "name": user.name or user_name,
                    "verified": True,  # OAuth пользователи считаются верифицированными
                    "event_type": "user_registered",
                    "role": user.role.value
                }

                message = aio_pika.Message(
                    body=json.dumps(user_event).encode(),
                    headers={"event_type": "user_events"},
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )

                await exchange.publish(
                    message,
                    routing_key="user.created"
                )

            except Exception as e:
                # Логируем ошибку, но не прерываем процесс авторизации
                print(f"[RabbitMQ] Failed to publish VK OAuth user event: {e}")

        jwt_token = await create_access_token({"sub": str(user.id), "role": user.role.value})

        response = RedirectResponse(settings.FRONTEND_URL) # type: ignore
        response.set_cookie(
            key=COOKIE_NAME,
            value=jwt_token,
            httponly=True,
            secure=True,
            samesite="none",
            domain=".rosdk.ru",   # ← если фронт и бэк на поддоменах
            path="/",
            max_age=3600 * 24 * 7
        )

        response.delete_cookie(key="vk_code_verifier")
        return response 
