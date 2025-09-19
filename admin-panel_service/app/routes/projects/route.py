from fastapi import APIRouter
from app.clients.projects.projects_client import ProjectsClient
import json

router = APIRouter(prefix="/admin/projects")
projects_client = ProjectsClient()

@router.get("/")
async def get_all():
    response = await projects_client.call("projects.get_all", json.dumps({}))
    return json.loads(response)

@router.get("/{project_id}")
async def get_project(project_id: int):
    response = await projects_client.call("projects.get", json.dumps({"project_id": project_id}))
    return json.loads(response)
