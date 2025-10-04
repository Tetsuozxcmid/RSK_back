from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db  
from cruds.crud import ZvezdaCRUD
from schemas.proj import (
    ProjectCreate, ProjectRead,
    TaskRead, TaskStartRequest, TaskSubmissionCreate, TaskSubmissionRead
) 


router = APIRouter(prefix="/zvezda", tags=["Zvezda"])


@router.post("/projects", response_model=ProjectRead)
async def create_project(project_data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = await ZvezdaCRUD.create_project(db, project_data)
    return project



@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await ZvezdaCRUD.get_project(db, project_id)
    return project



@router.get("/projects", response_model=list[ProjectRead])
async def list_projects(organization_name: str = None, db: AsyncSession = Depends(get_db)):
    projects = await ZvezdaCRUD.list_projects(db, organization_name)
    return projects



@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await ZvezdaCRUD.get_task(db, task_id)
    return task



@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    data: TaskStartRequest,
    db: AsyncSession = Depends(get_db)
):
    task = await ZvezdaCRUD.start_task(
        db=db,
        task_id=task_id,
        team_id=data.team_id,
        leader_id=data.leader_id
    )
    return task


@router.post("/tasks/{task_id}/submit")
async def submit_task(task_id: int, data: TaskSubmissionRead, db: AsyncSession = Depends(get_db)):
    submission = await ZvezdaCRUD.submit_task(
        db, task_id, team_id=data.team_id, text_description=data.text_description, result_url=data.result_url
    )
    return {"submission_id": submission.id, "status": submission.status.value}


@router.get("/tasks/{task_id}/submissions")
async def get_task_submissions(task_id: int, db: AsyncSession = Depends(get_db)):
    submissions = await ZvezdaCRUD.get_task_submissions(db, task_id)
    return submissions

