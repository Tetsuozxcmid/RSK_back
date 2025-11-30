import logging
import httpx
from fastapi import HTTPException
from config import settings

class UserProfileClient:
    @staticmethod
    async def get_user_profile(user_id: int):
        try:
            print(f"DEBUG UserProfileClient: Making batch request for user {user_id}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.USER_PROFILE_URL}/profile_interaction/get_users_batch",
                    json={"user_ids": [user_id]},  
                    timeout=5.0,
                )
                
                print(f"DEBUG UserProfileClient: Batch response: {response.status_code} - {response.text}")
                
                if response.status_code == 200:
                    users_data = response.json()

                    user_data = users_data.get(str(user_id))
                    print(f"DEBUG UserProfileClient: Found user data: {user_data}")
                    return user_data
                else:
                    print(f"DEBUG UserProfileClient: Batch request failed: {response.status_code}")
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
        
    @staticmethod
    async def update_user_team(user_id: int, team_name: str, team_id: int):
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.USER_PROFILE_URL}/profile_interaction/update_user_profile_joined_team/"
                logging.info(f"Calling profile service: {url}")
                
                response = await client.post(
                    url,
                    json={
                        "user_id": user_id,  
                        "team": team_name,
                        "team_id": team_id
                    },
                    timeout=5.0,
                )
                
                logging.info(f"Profile service response: {response.status_code} - {response.text}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"Failed to update user team: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logging.error(f"Error updating user team: {str(e)}")
            return None
        

    @staticmethod
    async def update_user_org(user_id: int, organization_name: str, organization_id: int):
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.USER_PROFILE_URL}/profile_interaction/update_user_profile_joined_org/"
                logging.info(f"Calling profile service: {url}")
                
                response = await client.post(
                    url,
                    json={
                        "user_id": user_id,  
                        "Organization": organization_name,
                        "Organization_id": organization_id
                    },
                    timeout=5.0,
                )
                
                logging.info(f"Profile service response: {response.status_code} - {response.text}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"Failed to update user team: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logging.error(f"Error updating user team: {str(e)}")
            return None