import httpx
from typing import Optional, Dict, List
from config import settings
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
import logger
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

    async def get_all_users(self) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                print(f"Fetching all users from {self.auth_url}")
                response = await client.get(
                    f"{self.auth_url}/users_interaction/get_users/",
                    timeout=30.0,
                )

                if response.status_code == 200:
                    users = response.json()
                    print(f"Received {len(users)} users from auth_service")
                    return users
                else:
                    print(
                        f"Failed to fetch users from auth_service: {response.status_code}"
                    )
                    return []
            except Exception as e:
                print(f"Error fetching users from auth service: {e}")
                return []

    async def update_user_learning_status(self, user_id: int, learning: bool) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                print(f"Updating learning status for user {user_id} to {learning}")

                full_url = (
                    f"{self.profile_url}/profile_interaction/update_learning_status/"
                )
                print(f"🌐 Full URL: {full_url}")

                response = await client.post(
                    full_url,
                    json={"user_id": user_id, "is_learned": learning},
                    headers={
                        "Authorization": f"Bearer {settings.SECRET_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    print(f"✅ Successfully updated user {user_id} to {learning}")
                    return True
                else:
                    print(f"❌ Failed to update user {user_id}: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False

            except Exception as e:
                print(f"❌ Exception updating user {user_id}: {e}")
                return False

    async def get_user_learning_status(self, user_id: int) -> Optional[bool]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.profile_url}/profile_interaction/get_profile/",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {settings.SECRET_KEY}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    user_data = response.json()
                    if isinstance(user_data, list) and len(user_data) > 0:
                        return user_data[0].get("is_learned", False)
                    elif isinstance(user_data, dict):
                        return user_data.get("is_learned", False)
                    return False
                else:
                    logger.error(f"Failed to get user learning status: {response.status_code}")
                    return None

            except Exception as e:
                logger.error(f"Error getting user learning status: {e}")
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
