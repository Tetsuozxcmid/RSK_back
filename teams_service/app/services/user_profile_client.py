import httpx
from fastapi import HTTPException
from config import settings

class UserProfileClient:
    @staticmethod
    async def get_user_profile(user_id: int):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.USER_PROFILE_URL}/profile_interaction/get_user_by_id/{user_id}",
                    timeout=5.0,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            print(f"Error fetching user profile: {str(e)}")
            return None
    
    @staticmethod
    async def get_users_profiles(user_ids: list[int]):
        try:
            async with httpx.AsyncClient() as client:
                
                response = await client.post(
                    f"{settings.USER_PROFILE_URL}/profile_interaction/get_users_batch",
                    json={"user_ids": user_ids},  
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
                    
        except Exception as e:
            print(f"Error fetching users profiles: {str(e)}")
            return {}