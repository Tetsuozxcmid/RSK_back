from fastapi import APIRouter

from clients.projects.projects_client import ProjectsClient

router = APIRouter(prefix="/admin/projects")
project_client = ProjectsClient()

@router.get("/")
async def get_all():
    response = await project_client.get_all_projects()
    return response

@router.get("/{project_id}")
async def get_project(project_id: int):
    response = await project_client.get_project(project_id)
    return response

