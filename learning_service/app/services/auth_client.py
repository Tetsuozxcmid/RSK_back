import httpx
from typing import Optional, Dict, List
from config import settings
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt

import logging
logger = logging.getLogger(__name__)
ALGORITHM = settings.ALGORITHM

ROLE_HIERARCHY = {
    "moder": 1,   # базовый уровень модерации
    "admin": 2,   # admin имеет все права moder + свои
}

class AuthServiceClient:
    def __init__(self):
        self.auth_url = settings.AUTH_SERVICE_URL
        self.profile_url = settings.PROFILE_SERVICE_URL

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                print(f"Fetching user {user_id} from {self.auth_url}")
                response = await client.get(
                    f"{self.auth_url}/users_interaction/get_user_by_id/{user_id}",
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to fetch user: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Error fetching user from auth service: {e}")
                return None

    async def get_user_email(self, user_id: int) -> Optional[str]:
        user_data = await self.get_user_by_id(user_id)
        if user_data:
            return user_data.get("email")
        return None

    async def get_all_users(self, admin_cookie: str = None) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                print(f"Fetching all users from {self.auth_url}")
                
                # Подготавливаем заголовки
                headers = {
                    "Content-Type": "application/json",
                }
                
                # Подготавливаем куки
                cookies = {}
                if admin_cookie:
                    cookies["users_access_token"] = admin_cookie
                
                print(f"Using cookies: {cookies}")
                
                response = await client.get(
                    f"{self.auth_url}/users_interaction/get_users/",
                    headers=headers,
                    cookies=cookies,
                    timeout=30.0,
                )

                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    users = response.json()
                    print(f"✅ Received {len(users)} users from auth_service")
                    return users
                else:
                    print(f"❌ Failed to fetch users: {response.status_code}")
                    print(f"Response: {response.text}")
                    return []
            except Exception as e:
                print(f"❌ Error fetching users from auth service: {e}")
                return []

    async def update_user_learning_status(self, user_id: int, learning: bool) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                full_url = f"{self.profile_url}/profile_interaction/update_learning_status/"
                logger.info(f"📤 Updating learning status for user {user_id} to {learning}")
                
                response = await client.post(
                    full_url,
                    json={"user_id": user_id, "is_learned": learning},
                    headers={
                        "Authorization": f"Bearer {settings.SECRET_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )

                logger.info(f"📡 Response status: {response.status_code}")
                logger.info(f"📦 Response body: {response.text}")

                if response.status_code == 200:
                    logger.info(f"✅ Successfully updated user {user_id} to {learning}")
                    return True
                else:
                    logger.error(f"❌ Failed to update user {user_id}: {response.status_code}")
                    return False

            except Exception as e:
                logger.error(f"❌ Exception updating user {user_id}: {e}")
                return False

    async def get_user_learning_status(self, user_id: int, admin_cookie: str = None) -> Optional[bool]:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.profile_url}/profile_interaction/get_profile/"
                logger.info("="*60)
                logger.info(f"🔍 GET_USER_LEARNING_STATUS CALLED for user {user_id}")
                logger.info(f"📤 URL: {url}")
                logger.info(f"📤 Admin cookie provided: {bool(admin_cookie)}")
                
                # Подготавливаем заголовки и куки
                headers = {
                    "Content-Type": "application/json",
                }
                cookies = {}
                
                if admin_cookie:
                    cookies["users_access_token"] = admin_cookie
                    logger.info("🍪 Using admin cookie for authentication")
                    logger.info(f"🍪 Cookie value: {admin_cookie[:20]}...")  # Логируем начало куки
                else:
                    headers["Authorization"] = f"Bearer {settings.SECRET_KEY}"
                    logger.info("🔑 Using Bearer token for authentication")
                
                logger.info(f"📤 Request params: user_id={user_id}")
                logger.info(f"📤 Headers: {headers}")
                logger.info(f"📤 Cookies: {cookies}")
                
                # Выполняем запрос
                response = await client.get(
                    url,
                    params={"user_id": user_id},
                    headers=headers,
                    cookies=cookies,
                    timeout=10.0,
                    follow_redirects=True
                )
                
                logger.info(f"📡 Response status: {response.status_code}")
                logger.info(f"📡 Response headers: {dict(response.headers)}")
                logger.info(f"📦 Response body: {response.text}")
                logger.info("="*60)

                if response.status_code == 200:
                    try:
                        user_data = response.json()
                        logger.info(f"📊 Parsed JSON type: {type(user_data)}")
                        logger.info(f"📊 Parsed JSON: {user_data}")
                        
                        # Profile сервис возвращает одного пользователя как словарь
                        if isinstance(user_data, dict):
                            logger.info(f"📊 Response is dict with keys: {list(user_data.keys())}")
                            result = user_data.get("is_learned", False)
                            logger.info(f"✅ Found status in dict: {result}")
                            return result
                        # Если вернулся список
                        elif isinstance(user_data, list):
                            logger.info(f"📊 Response is list with length: {len(user_data)}")
                            if len(user_data) > 0:
                                # Ищем пользователя с нужным id
                                for i, u in enumerate(user_data):
                                    logger.info(f"  Item {i}: {u}")
                                    if isinstance(u, dict) and u.get("id") == user_id:
                                        result = u.get("is_learned", False)
                                        logger.info(f"✅ Found user {user_id} in list at index {i}, status: {result}")
                                        return result
                                logger.warning(f"⚠️ User {user_id} not found in response list")
                            else:
                                logger.warning("⚠️ Empty list returned")
                            return None
                        else:
                            logger.warning(f"⚠️ Unexpected response type: {type(user_data)}")
                            return None
                    except ValueError as e:
                        logger.error(f"❌ Failed to parse JSON response: {e}")
                        return None
                elif response.status_code == 401:
                    logger.error("❌ Authentication failed - invalid token or cookie")
                    return None
                elif response.status_code == 404:
                    logger.error(f"❌ User {user_id} not found in profile service")
                    return None
                else:
                    logger.error(f"❌ Failed to get user learning status: {response.status_code}")
                    return None

            except httpx.RequestError as e:
                logger.error(f"❌ Network error getting user learning status: {e}", exc_info=True)
                return None
            except Exception as e:
                logger.error(f"❌ Unexpected error getting user learning status: {e}", exc_info=True)
                return None
            
    async def bulk_update_learning_status(self, users_data: List[Dict]) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.profile_url}/profile_interaction/bulk_update_learning/",
                    json={"users": users_data},
                    headers={
                        "Authorization": f"Bearer {settings.SECRET_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Bulk updated {result.get('updated', 0)} users")
                    return True
                else:
                    logger.error(f"❌ Bulk update failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Exception in bulk update: {e}")
                return False


async def get_current_user_role(request: Request) -> str:
    token = request.cookies.get("users_access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing in cookies"
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role not found in token",
            )

        return user_role

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def require_role(required_role: str):
    def role_checker(user_role: str = Depends(get_current_user_role)):
        if required_role == "moder":
            if user_role not in ["moder", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions. Required: moder or admin",
                )
        
        elif required_role == "admin":
            if user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions. Required: admin",
                )
        
        elif user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return user_role

    return role_checker


get_moderator = require_role("moder")
get_admin = require_role("admin")
auth_client = AuthServiceClient()
