from fastapi import APIRouter

from clients.tasks.tasks_client import TasksClient

router = APIRouter(prefix="/admin/tasks")
tasks_client = TasksClient()

@router.get("/")
async def get_all():
    response = await tasks_client.get_all_tasks()
    return response

@router.get("/{task_id}")
async def get_task(task_id: int):
    response = await tasks_client.get_task_by_id(task_id)
    return response

@router.put("/{task_id}")
async def update_task(task_id: int, status: str):
    response = await tasks_client.change_status(task_id, status)
    return response

