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

    # Validate required parameters
    if not code:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=code_missing")
    
    if not device_id:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=device_id_missing")

    code_verifier = request.cookies.get("vkid_sdk:codeVerifier")
    if not code_verifier:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=code_verifier_not_found")

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://id.vk.com/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": settings.VK_REDIRECT_URI,
                "client_id": settings.VK_APP_ID,
                "client_secret": settings.VK_APP_SECRET,
                "device_id": str(device_id)  # Ensure it's a string
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token_data = token_resp.json()
        print(f"Token response: {token_data}")
        
        # Check for errors in token response
        if "error" in token_data:
            error_msg = token_data.get("error_description", token_data.get("error"))
            print(f"VK token error: {error_msg}")
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=vk_token_error")
        
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=token_not_received")

    # Get user info
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://id.vk.ru/oauth2/user_info",
            params={
                "client_id": settings.VK_APP_ID,
                "access_token": access_token
            }
        )
        data = user_resp.json()
        print(f"User info response: {data}")
        
        # Check for errors in user info response
        if "error" in data:
            error_msg = data.get("error_description", data.get("error"))
            print(f"VK user info error: {error_msg}")
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=vk_user_info_error")
        
        user_data = data.get("user")
        if not user_data:
            print(f"No user data in response: {data}")
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=user_data_missing")

        user_id = user_data.get("user_id")
        user_first_name = user_data.get("first_name", "")
        user_last_name = user_data.get("last_name", "")
        user_email = user_data.get("email")

        if not user_id:
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=user_id_missing")

        user_name = f"{user_first_name} {user_last_name}".strip()

        # Create or get user
        user = await user_crud.create_oauth_user(
            db=db,
            email=user_email,
            name=user_name,
            provider="vk",
            provider_id=str(user_id),
            role=UserRole.STUDENT
        )
        
        # Publish user event to RabbitMQ
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
                "verified": True,
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
            print(f"[RabbitMQ] Failed to publish VK OAuth user event: {e}")

        # Create JWT and set cookie
        jwt_token = await create_access_token({"sub": str(user.id), "role": user.role.value})

        response = RedirectResponse(settings.FRONTEND_URL) # type: ignore
        response.set_cookie(
            key=COOKIE_NAME,
            value=jwt_token,
            httponly=True,
            secure=True,
            samesite="none",
            domain=".rosdk.ru",
            path="/",
            max_age=3600 * 24 * 7
        )

        response.delete_cookie(key="vkid_sdk:codeVerifier")
        return response
