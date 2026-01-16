from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import secrets
import httpx
import aio_pika
import json

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import UserRole
from services.jwt import create_access_token
from services.rabbitmq import get_rabbitmq_connection
from config import settings

vk_router = APIRouter(prefix="/auth/vk", tags=["VK OAuth"])
user_crud = UserCRUD()

COOKIE_NAME = "users_access_token"
STATE_COOKIE = "vkid_sdk:state"


# ================= START =================

@vk_router.get("/start")
async def vk_start():
    state = secrets.token_urlsafe(16)

    params = {
        "client_id": settings.VK_APP_ID,
        "redirect_uri": settings.VK_REDIRECT_URI,
        "response_type": "code",
        "scope": "",
        "state": state
    }

    url = "https://id.vk.ru/authorize?" + urlencode(params)

    response = RedirectResponse(url)

    # CSRF-защита
    response.set_cookie(
        key=STATE_COOKIE,
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600
    )

    return response


# ================= CALLBACK =================

@vk_router.get("/callback")
async def vk_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    rabbitmq: aio_pika.abc.AbstractRobustConnection = Depends(get_rabbitmq_connection)
):
    error = request.query_params.get("error")
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error={error}")

    # Проверка CSRF state
    cookie_state = request.cookies.get(STATE_COOKIE)
    if not cookie_state or cookie_state != state:
        return RedirectResponse(f"{settings.FRONTEND_URL}?error=invalid_state")

    # ===== 1. CODE → ACCESS TOKEN =====
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth.vk.com/access_token",
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.VK_REDIRECT_URI,
                "client_id": settings.VK_APP_ID,
                "client_secret": settings.VK_APP_SECRET,
            }
        )

    token_data = token_resp.json()
    print("VK TOKEN:", token_data)

    access_token = token_data.get("access_token")
    if not access_token:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error=token_not_received"
        )

    # ===== 2. GET USER INFO =====
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://id.vk.ru/oauth2/user_info",
            params={
                "client_id": settings.VK_APP_ID,
                "access_token": access_token
            }
        )

    data = user_resp.json()
    print("VK USER:", data)

    user = data.get("user")
    if not user:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}?error=user_not_received"
        )

    user_id = user.get("user_id")
    user_first_name = user.get("first_name")
    user_last_name = user.get("last_name")
    user_email = user.get("email")

    user_name = f"{user_first_name} {user_last_name}"

    # ===== 3. CREATE / GET USER =====
    user = await user_crud.create_oauth_user(
        db=db,
        email=user_email,
        name=user_name,
        provider="vk",
        provider_id=str(user_id),
        role=UserRole.STUDENT
    )

    # ===== 4. EVENT IN RABBITMQ =====
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

    # ===== 5. CREATE YOUR JWT =====
    jwt_token = await create_access_token({
        "sub": str(user.id),
        "role": user.role.value
    })

    # ===== 6. FINAL REDIRECT =====
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

    # удалить state
    response.delete_cookie(STATE_COOKIE)

    return response