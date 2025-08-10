import httpx
from fastapi import HTTPException
from config import settings

class OrgsClient:
    @staticmethod
    async def check_organization_exists(org_name: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://rsk_orgs_app:8005/organizations/exists/{org_name}",
                    timeout=5.0  
                )
                
                if response.status_code == 200:
                    return response.json().get("exists", False)
                
                if response.status_code == 404:
                    return False
                    
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Organization service error: {response.text}"
                )
                
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Organization service is unavailable"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking organization: {str(e)}"
            )