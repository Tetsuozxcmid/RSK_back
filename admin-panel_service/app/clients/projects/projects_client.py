import json
from fastapi import HTTPException

from app.services.rabbitmq_rpc_client import RabbitMQRPCClient


class ProjectsClient:
    def __init__(self):
        self.rabbit_rpc_client = RabbitMQRPCClient()

    async def get_all_projects(self):
        try:
            response = await self.rabbit_rpc_client.call("projects.get_all", json.dumps({}))
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

    async def get_project(self, project_id: int):
        try:
            response = await self.rabbit_rpc_client.call("projects.get", json.dumps({"project_id": project_id}))
            return json.loads(response)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching project {project_id}: {str(e)}")
