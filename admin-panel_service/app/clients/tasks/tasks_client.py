import httpx
from fastapi import HTTPException
from config import settings

class TasksClient:
    def __init__(self):
        self.url = f"{settings.WORKSHOP_URL}/tasks"

    async def get_all_tasks(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch tasks"
                )
            
            return response.json()
        
    async def get_task_by_id(self, task_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/{task_id}")
            
            if response.status_code!= 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch task"
                )
            
            return response.json()

    async def change_status(self, task_id: int, status: str):
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.url}/{task_id}",
                json={"status": status}
            )
            
            if response.status_code!= 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to change task status"
                )
            
            return response.json()