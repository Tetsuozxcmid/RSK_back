from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import UserRole
from services.jwt import create_access_token
from services.oauth_profile import build_user_registered_event, normalize_vk_profile
from services.profile_client import UserProfileClient
from services.rabbitmq import get_rabbitmq_connection

from config import settings

import httpx
import aio_pika
import json

vk_router = APIRouter(prefix="/auth/vk", tags=["VK OAuth"])
COOKIE_NAME = "users_access_token"


@vk_router.get("/callback")
async def vk_callback(
    request: Request,
    device_id: str | int = None,
    code: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db),
    rabbitmq: aio_pika.abc.AbstractRobustConnection = Depends(get_rabbitmq_connection),
):
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error={error}")

    code_verifier = request.cookies.get("vkid_sdk:codeVerifier")
    if not code_verifier:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error=code_verifier_not_found"
        )

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
                "device_id": device_id,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_resp.json()
        print(token_data)
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{settings.FRONTEND_URL}?error=token_not_received")

    async with httpx.AsyncClient() as client:
        user_resp = await client.post(
            "https://id.vk.ru/oauth2/user_info",
            data={"client_id": settings.VK_APP_ID, "access_token": access_token},
        )
        data = user_resp.json()
        print(f"[VK DEBUG] user_info payload: {data}")

    provider_user = data.get("user") or {}
    provider_user_id = provider_user.get("user_id")
    if not provider_user_id:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=user_not_received")

    oauth_profile = normalize_vk_profile(provider_user)
    print(f"[VK DEBUG] Received email: {oauth_profile['email']}")

    user, created = await UserCRUD.create_oauth_user(
        db=db,
        name=oauth_profile["full_name"],
        provider="vk",
        provider_id=str(provider_user_id),
        email=oauth_profile["email"] or None,
        role=UserRole.STUDENT,
    )
    resolved_username = user.login or f"user{user.id}"

    await UserProfileClient.sync_oauth_profile(
        user_id=user.id,
        email=user.email or oauth_profile["email"],
        username=resolved_username,
        first_name=oauth_profile["first_name"],
        last_name=oauth_profile["last_name"],
        patronymic=oauth_profile["patronymic"],
        full_name=user.name or oauth_profile["full_name"],
        role=user.role.value,
        auth_provider="vk",
    )

    if created:
        try:
            channel = await rabbitmq.channel()
            exchange = await channel.declare_exchange(
                "user_events", type="direct", durable=True
            )

            user_event = build_user_registered_event(
                user_id=user.id,
                email=user.email or oauth_profile["email"],
                username=resolved_username,
                first_name=oauth_profile["first_name"],
                last_name=oauth_profile["last_name"],
                patronymic=oauth_profile["patronymic"],
                full_name=user.name or oauth_profile["full_name"],
                role=user.role.value,
                auth_provider="vk",
            )

            message = aio_pika.Message(
                body=json.dumps(user_event).encode(),
                headers={"event_type": "user_events"},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )

            await exchange.publish(message, routing_key="user.created")
        except Exception as e:
            print(f"[RabbitMQ] Failed to publish VK OAuth user event: {e}")

    jwt_token = await create_access_token(
        {"sub": str(user.id), "role": user.role.value}
    )

    response = RedirectResponse(settings.FRONTEND_URL)
    response.set_cookie(
        key=COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="none",
        domain=".rosdk.ru",
        path="/",
        max_age=3600 * 24 * 7,
    )

    response.delete_cookie(key="vkid_sdk:codeVerifier")
    return response
