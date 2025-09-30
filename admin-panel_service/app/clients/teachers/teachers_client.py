import json
from fastapi import HTTPException

from app.services.rabbitmq_rpc_client import RabbitMQRPCClient

class TeachersClient:
    def __init__(self):
        self.rabbit_rpc_client = RabbitMQRPCClient()

    async def get_all_teachers(self):
        return await self._make_call("teachers.get_all", {})

    async def get_unapproved_teachers(self):
        return await self._make_call("teachers.get_all", {"approved": False})

    async def get_approved_teachers(self):
        return await self._make_call("teachers.get_all", {"approved": True})

    async def get_teacher_by_id(self, teacher_id: int):
        return await self._make_call("teachers.get", {"teacher_id": teacher_id})
    

    async def approve_teacher(self, teacher_id: int):
        return await self._make_call("teachers.update", {"teacher_id": teacher_id, "approved": True})

    async def reject_teacher(self, teacher_id: int):
        return await self._make_call("teachers.update", {"teacher_id": teacher_id, "approved": False})
    
    

    async def _make_call(self, routing_key: str, payload: dict):
        try:
            response = await self.rabbit_rpc_client.call(routing_key, json.dumps(payload))
            return json.loads(response)
        except Exception as e:
            action = routing_key.split('.')[-1]
            raise HTTPException(status_code=500, detail=f"Error {action} teachers: {str(e)}")