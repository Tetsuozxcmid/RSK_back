from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from aio_pika.abc import AbstractRobustConnection
import httpx
import aio_pika
import json
import time

from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import User, UserRole
from services.jwt import create_access_token
from services.rabbitmq import get_rabbitmq_connection
from config import settings

yandex_router = APIRouter(prefix="/auth/yandex", tags=["Yandex OAuth"])

COOKIE_NAME = "users_access_token"


@yandex_router.get("/login")
async def yandex_login():
    url = (
        "https://oauth.yandex.com/authorize?"
        "response_type=code"
        f"&client_id={settings.YANDEX_CLIENT_ID}"
        f"&redirect_uri={settings.YANDEX_REDIRECT_URI}"
    )
    return RedirectResponse(url)


@yandex_router.get("/callback")
async def yandex_callback(
    response: Response,
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection),
):
    print(f"[YANDEX DEBUG {time.time()}] Callback started, code: {code}")

    if error:
        return RedirectResponse(f"{settings.YANDEX_FRONTEND_URL}?error={error}")

    if not code:
        return RedirectResponse(f"{settings.YANDEX_FRONTEND_URL}?error=code_missing")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth.yandex.com/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.YANDEX_CLIENT_ID,
                "client_secret": settings.YANDEX_CLIENT_SECRET,
                "redirect_uri": settings.YANDEX_REDIRECT_URI,
            },
        )

        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            print(f"[YANDEX ERROR] Token response: {token_data}")
            return RedirectResponse(f"{settings.YANDEX_FRONTEND_URL}?error=token_not_received")

        user_resp = await client.get(
            "https://login.yandex.ru/info?format=json",
            headers={"Authorization": f"OAuth {access_token}"}
        )
        user_data = user_resp.json()

    email = user_data.get("default_email")
    if not email:
        return RedirectResponse(f"{settings.YANDEX_FRONTEND_URL}?error=email_not_provided")

    result = await db.execute(
        select(User).where(
            User.provider_id == str(user_data["id"]),
            User.auth_provider == "yandex"
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        user = existing_user
        print(f"[YANDEX DEBUG] User already exists, id: {user.id}")
    else:
        user = await UserCRUD.create_oauth_user(
            db=db,
            email=email,
            name=user_data.get("real_name") or user_data.get("display_name") or "",
            provider="yandex",
            provider_id=str(user_data["id"]),
            role=UserRole.STUDENT
        )

        if not user.login:
            user.login = f"user{user.id}"
            await db.commit()
            await db.refresh(user)

        print(f"[YANDEX DEBUG] New user created, id: {user.id}")

    print(f"[YANDEX DEBUG] Sending user.created event, user_id: {user.id}")

    channel = await rabbitmq.channel()
    exchange = await channel.declare_exchange("user_events", type="direct", durable=True)

    user_event = {
        "user_id": user.id,
        "email": user.email,
        "username": user.login,
        "name": user.name,
        "verified": True,
        "event_type": "user_registered",
        "role": user.role.value,
    }

    message = aio_pika.Message(
        body=json.dumps(user_event).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        headers={"event_type": "user_registered"},
    )

    await exchange.publish(message, routing_key="user.created")
    print(f"[YANDEX DEBUG] Event published for user_id: {user.id}")

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
    max_age=3600 * 24 * 7
)

    print(f"[YANDEX DEBUG] Callback completed for user_id: {user.id}")
    return response
