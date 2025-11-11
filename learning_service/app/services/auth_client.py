import httpx
from typing import Optional, Dict
from config import settings

class AuthServiceClient:
    def __init__(self):
        self.base_url = settings.AUTH_SERVICE_URL
        
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users_interaction/get_user_by_id/{user_id}",
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Error fetching user from auth service: {e}")
                return None
    
    async def get_user_email(self, user_id: int) -> Optional[str]:
        user_data = await self.get_user_by_id(user_id)
        if user_data:
            return user_data.get("email")
        return None

auth_client = AuthServiceClient()