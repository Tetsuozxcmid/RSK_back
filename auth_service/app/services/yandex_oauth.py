from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import User, UserRole
from services.jwt import create_access_token

import os

yandex_router = APIRouter(prefix="/auth/yandex", tags=["Yandex OAuth"])


CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI")
FRONTEND_URL = os.getenv("YANDEX_FRONTEND_URL")
COOKIE_NAME = "users_access_token"  

@yandex_router.get("/login")
async def yandex_login():

    url = (
        f"https://oauth.yandex.com/authorize?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url)

@yandex_router.get("/callback")
async def yandex_callback(
    response: Response, 
    code: str = None, 
    error: str = None, 
    db: AsyncSession = Depends(get_db)
):

    if error:
        return RedirectResponse(f"{FRONTEND_URL}?error={error}")


    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth.yandex.com/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{FRONTEND_URL}?error=token_not_received")


        headers = {"Authorization": f"OAuth {access_token}"}
        user_resp = await client.get("https://login.yandex.ru/info?format=json", headers=headers)
        user_data = user_resp.json()


    result = await db.execute(
        select(User).where(User.provider_id == str(user_data["id"]), User.auth_provider == "yandex")
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        user = existing_user
    else:
        user = await UserCRUD.create_oauth_user(
            db=db,
            email=user_data.get("default_email"),
            name=user_data.get("real_name") or user_data.get("display_name"),
            provider="yandex",
            provider_id=user_data["id"],
            role=UserRole.STUDENT
        )



    jwt_token = await create_access_token({"sub": str(user.id), "role": user.role.value})


    response = RedirectResponse(FRONTEND_URL)
    response.set_cookie(
        key=COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        secure=False,   
        samesite="lax",
        max_age=3600*24*7  
    )
    return response
