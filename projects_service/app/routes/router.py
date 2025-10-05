from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.crud import ZvezdaCRUD
from services.service import get_current_user
from schemas.proj import (
    ProjectCreate, ProjectRead, TaskCreate, TaskOut,
    TaskRead, TaskStartRequest, TaskSubmissionRead
)

router = APIRouter(prefix="/zvezda", tags=["Zvezda"])


# === PROJECTS ===
@router.post("/projects", response_model=ProjectRead)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    return await ZvezdaCRUD.create_project(db, project_data)


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    return await ZvezdaCRUD.get_project(db, project_id)


@router.get("/projects", response_model=List[ProjectRead])
async def list_projects(
    organization_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    return await ZvezdaCRUD.list_projects(db, organization_name)


# === TASKS ===
@router.post("/projects/{project_id}/tasks", response_model=TaskOut)
async def create_task(
    project_id: int,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return await ZvezdaCRUD.create_task(db, task_in, project_id)


@router.get("/tasks", response_model=List[TaskOut])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    project_id: Optional[int] = None
):
    return await ZvezdaCRUD.list_tasks(db, project_id)


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    return await ZvezdaCRUD.get_task(db, task_id)


@router.post("/tasks/{task_id}/start")
async def start_task(task_id: int, request: Request, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)):
    task = await ZvezdaCRUD.start_task(db=db, task_id=task_id, user_id=user_id, request=request)
    return task


@router.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: int,
    data: TaskSubmissionRead,
    db: AsyncSession = Depends(get_db)
):
    submission = await ZvezdaCRUD.submit_task(
        db, task_id,
        team_id=data.team_id,
        text_description=data.text_description,
        result_url=data.result_url
    )
    return {"submission_id": submission.id, "status": submission.status.value}


@router.get("/tasks/{task_id}/submissions")
async def get_task_submissions(task_id: int, db: AsyncSession = Depends(get_db)):
    return await ZvezdaCRUD.get_task_submissions(db, task_id)


