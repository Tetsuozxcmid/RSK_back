from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from cruds.crud import ZvezdaCRUD
from services.service import get_current_user
from services.auth_client import require_role
from services.teams_client import TeamsClient
from services.auth_client import get_moderator
from db.models.projects import TaskStatus
from schemas.proj import (
    ModeratorTaskRead,
    ProjectCreate,
    ProjectRead,
    TaskCreate,
    TaskOut,
    TaskReviewRequest,
    TaskSubmitRequest,
    TaskSubmissionRead,
)


router = APIRouter(prefix="/zvezda", tags=["Zvezda"])



@router.post("/projects", response_model=ProjectRead)
async def create_project(
    data: ProjectCreate, db: AsyncSession = Depends(get_db), _=Depends(get_moderator)
):
    return await ZvezdaCRUD.create_project(db, data)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_moderator),
):
    return await ZvezdaCRUD.update_project(db, project_id, data)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_moderator)
):
    await ZvezdaCRUD.delete_project(db, project_id)
    return {"status": "deleted"}


@router.post("/projects/{project_id}/tasks", response_model=TaskOut)
async def create_task(
    project_id: int,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_moderator),
):
    return await ZvezdaCRUD.create_task(db, data, project_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_moderator),
):
    return await ZvezdaCRUD.update_task(db, task_id, data)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_moderator)
):
    await ZvezdaCRUD.delete_task(db, task_id)
    return {"status": "deleted"}



@router.get("/moderator/tasks", response_model=List[ModeratorTaskRead])
async def get_moder_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    _=Depends(get_moderator),
):
    return await ZvezdaCRUD.get_tasks_for_review(db, user_id)


@router.post("/moderator/{submission_id}/review")
async def review_task(
    submission_id: int,
    data: TaskReviewRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    _=Depends(get_moderator),
):
    return await ZvezdaCRUD.review_submission(
        db,
        submission_id,
        user_id,
        data.status,
        data.description,
    )



@router.get("/projects", response_model=List[ProjectRead])
async def list_projects(
    organization_id: Optional[int] = None,  
    db: AsyncSession = Depends(get_db)
):
    return await ZvezdaCRUD.list_projects(db, organization_id)


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    return await ZvezdaCRUD.get_project(db, project_id)


@router.get("/tasks", response_model=List[TaskOut])
async def list_tasks(
    db: AsyncSession = Depends(get_db), project_id: Optional[int] = None
):
    return await ZvezdaCRUD.list_tasks(db, project_id)


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await ZvezdaCRUD.start_task(db, task_id, user_id, request)


@router.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: int,
    request: Request,
    data: TaskSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    is_leader, team_id = await TeamsClient.is_user_team_leader(request)
    if not is_leader:
        raise HTTPException(403, "Only leaders")
    return await ZvezdaCRUD.submit_task(
        db, task_id, team_id, data.text_description, data.result_url
    )
