import httpx
from typing import Optional, Dict
from config import settings

class AuthServiceClient:
    def __init__(self):
        self.base_url = settings.AUTH_SERVICE_URL
        
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                print(f"Fetching user {user_id} from {self.base_url}")
                response = await client.get(
                    f"{self.base_url}/users_interaction/get_user_by_id/{user_id}",
                    timeout=30.0
                )
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response text: {response.text}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"User data received: {user_data}")
                    print(f"Email in response: {user_data.get('email')}")
                    return user_data
                else:
                    print(f"Failed to fetch user: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Error fetching user from auth service: {e}")
                return None
    
    async def get_user_email(self, user_id: int) -> Optional[str]:
        user_data = await self.get_user_by_id(user_id)
        if user_data:
            email = user_data.get("email")
            print(f"Extracted email: {email}")
            return email
        return None

auth_client = AuthServiceClient()