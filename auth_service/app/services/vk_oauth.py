from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import UserRole
from services.jwt import create_access_token

from config import settings

import httpx

router = APIRouter(prefix="/auth/vk", tags=["vk_oauth"])
user_crud = UserCRUD()
COOKIE_NAME = "users_access_token"  

@router.get("/callback")
async def vk_callback(
    request: Request,
    device_id: str | int = None, # type: ignore
    code: str = None, # type: ignore
    error: str = None, # type: ignore
    db: AsyncSession = Depends(get_db)
):
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL_YANDEX}?error={error}")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth.vk.com/access_token",
            params={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.VK_REDIRECT_URI,
                "client_id": settings.VK_APP_ID,
                "client_secret": settings.VK_APP_SECRET,
                "device_id": device_id,
                "state": "get_token"
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{settings.FRONTEND_URL_YANDEX}?error=token_not_received")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://id.vk.ru/oauth2/user_info",
            params={
                "client_id": settings.VK_APP_ID,
                "access_token": access_token
            }
        )
        user_data = user_resp.json()
        user_info = user_data.get("user", {})

        user_id = user_info.get("user_id")
        user_first_name = user_info.get("first_name")
        user_email = user_info.get("email")

        user = await user_crud.create_oauth_user(
            db=db,
            email=user_email,
            name=user_first_name,
            provider="vk",
            provider_id=str(user_id),
            role=UserRole.STUDENT
        )

        jwt_token = await create_access_token({"sub": str(user.id), "role": user.role.value})


        response = RedirectResponse(settings.FRONTEND_URL) # type: ignore
        response.set_cookie(
            key=COOKIE_NAME,
            value=jwt_token,
            httponly=True,
            secure=False,   
            samesite="lax",
            max_age=3600*24*7  
        )
        return response