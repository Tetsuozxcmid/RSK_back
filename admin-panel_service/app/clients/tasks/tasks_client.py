import json
from fastapi import HTTPException
from config import settings

from app.services.rabbitmq_rpc_client import RabbitMQRPCClient

class TasksClient:
    def __init__(self):
        self.rabbit_rpc_client = RabbitMQRPCClient()

    async def get_all_tasks(self):
        try:
            response = await self.rabbit_rpc_client.call("tasks.get_all", json.dumps({}))
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")
        
    async def get_task_by_id(self, task_id: int):
        try:
            response = await self.rabbit_rpc_client.call("tasks.get", json.dumps({"task_id": task_id}))
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching task {task_id}: {str(e)}")
        
    async def change_status(self, task_id: int, status: str):
        try:
            response = await self.rabbit_rpc_client.call("tasks.update", json.dumps({"task_id": task_id, "status": status}))
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error changing status of task {task_id}: {str(e)}")
        

    