import httpx
from typing import Optional, Dict, List
from app.config import settings
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt

ALGORITHM = settings.ALGORITHM


class AuthServiceClient:
    def __init__(self):
        self.base_url = settings.AUTH_SERVICE_URL
        self.profile_service_url = settings.PROFILE_SERVICE_URL

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                print(f"Fetching user {user_id} from {self.base_url}")
                response = await client.get(
                    f"{self.base_url}/users_interaction/get_user_by_id/{user_id}",
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
                print(f"Fetching all users from {self.profile_service_url}")
                
                response = await client.post(
                    f"{self.profile_service_url}/profile_interaction/get_users_batch",
                    json=[],  
                    headers={
                        "Authorization": f"Bearer {settings.SECRET_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    users = response.json()
                    print(f"Received {len(users)} users")
                    return users
                else:
                    print(f"Failed to fetch users: {response.status_code}")
                    return []
            except Exception as e:
                print(f"Error fetching users from profile service: {e}")
                return []

    async def update_user_learning_status(self, user_id: int, learning: bool) -> bool:
        
        async with httpx.AsyncClient() as client:
            try:
             
                get_response = await client.get(
                    f"{self.profile_service_url}/profile_interaction/get_profile/?user_id={user_id}",
                    headers={"Authorization": f"Bearer {settings.SECRET_KEY}"},
                    timeout=10.0
                )
                
                if get_response.status_code != 200:
                    print(f"Failed to get user {user_id}: {get_response.status_code}")
                    return False
                
                user_data = get_response.json()
                
                
                response = await client.post(
                    f"{self.profile_service_url}/profile_interaction/update_profile/",
                    json={
                        "user_id": user_id,
                        "is_learned": learning
                    },
                    headers={
                        "Authorization": f"Bearer {settings.SECRET_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"Updated learning status for user {user_id} to {learning}")
                    return True
                else:
                    print(f"Failed to update learning status: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"Failed to update learning status for user {user_id}: {e}")
                return False

    async def get_user_learning_status(self, user_id: int) -> Optional[bool]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.profile_service_url}/profile_interaction/get_profile/?user_id={user_id}",
                    headers={"Authorization": f"Bearer {settings.SECRET_KEY}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return user_data.get("is_learned", False)
                else:
                    print(f"Failed to get user learning status: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"Error getting user learning status: {e}")
                return None


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
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return user_role

    return role_checker


get_moderator = require_role("moder")
auth_client = AuthServiceClient()