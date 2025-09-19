import httpx
from fastapi import HTTPException
from config import settings

class ProjectsClient:
    def __init__(self):
        self.url = f"{settings.WORKSHOP_URL}/projects"

    async def get_all_projects(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch projects"
                )
            
            return response.json()

    async def get_project(self, project_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/{project_id}")
            
            if response.status_code!= 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch project"
                )
            
            return response.json()