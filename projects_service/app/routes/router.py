from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from cruds.crud import ZvezdaCRUD
from services.service import get_current_user
from services.auth_client import require_role
from services.teams_client import TeamsClient
from db.models.projects import TaskStatus
from schemas.proj import (
    ProjectCreate,
    ProjectRead,
    TaskCreate,
    TaskOut,
    TaskSubmitRequest,
    TaskSubmissionRead,
)

# Зависимости для проверки ролей
get_admin = require_role("ADMIN")
get_moder = require_role("MODER")

router = APIRouter(prefix="/zvezda", tags=["Zvezda"])


# === АДМИНИСТРАТИВНЫЕ ФУНКЦИИ (ADMIN ONLY) ===

@router.post("/projects", response_model=ProjectRead)
async def create_project(
    project_data: ProjectCreate, 
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin)
):
    """Создание нового проекта (ADMIN)."""
    return await ZvezdaCRUD.create_project(db, project_data)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int, 
    project_data: ProjectCreate, 
    db: AsyncSession = Depends(get_db), 
    admin=Depends(get_admin)
):
    """Редактирование проекта (ADMIN)."""
    return await ZvezdaCRUD.update_project(db, project_id, project_data)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int, 
    db: AsyncSession = Depends(get_db), 
    admin=Depends(get_admin)
):
    """Удаление проекта (ADMIN)."""
    await ZvezdaCRUD.delete_project(db, project_id)
    return {"status": "Project deleted"}


@router.post("/projects/{project_id}/tasks", response_model=TaskOut)
async def create_task(
    project_id: int,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin)
):
    """Создание задания в проекте (ADMIN)."""
    return await ZvezdaCRUD.create_task(db, task_in, project_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin)
):
    """Редактирование задания (ADMIN)."""
    return await ZvezdaCRUD.update_task(db, task_id, task_data)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_admin)
):
    """Удаление задания (ADMIN)."""
    await ZvezdaCRUD.delete_task(db, task_id)
    return {"status": "Task deleted"}


# === МОДЕРСКИЕ ФУНКЦИИ (MODER ONLY) ===

@router.get("/moderator/tasks", response_model=List[TaskSubmissionRead])
async def get_tasks_for_review(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    moder=Depends(get_moder)
):
    """Получение 5 заданий на проверку на 10 минут (MODER)."""
    return await ZvezdaCRUD.get_tasks_for_review(db, user_id)


@router.post("/moderator/{submission_id}/review")
async def review_task(
    submission_id: int,
    status: TaskStatus, # ACCEPTED или REJECTED
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    moder=Depends(get_moder)
):
    """Принятие или отклонение задания (MODER)."""
    # Допустимы только статусы ACCEPTED или REJECTED
    if status not in [TaskStatus.ACCEPTED, TaskStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="Invalid review status")
        
    submission = await ZvezdaCRUD.review_submission(
        db, submission_id, user_id, status, description
    )
    # TODO: Здесь можно вызвать сервис отправки Email оповещений
    return {"status": "reviewed", "new_status": submission.status.value}


# === ОБЩИЕ ФУНКЦИИ (USERS/TEAMS) ===

@router.get("/projects", response_model=List[ProjectRead])
async def list_projects(
    organization_name: Optional[str] = None, 
    db: AsyncSession = Depends(get_db)
):
    return await ZvezdaCRUD.list_projects(db, organization_name)


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    return await ZvezdaCRUD.get_project(db, project_id)


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
async def start_task(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await ZvezdaCRUD.start_task(
        db=db, task_id=task_id, user_id=user_id, request=request
    )


@router.post("/tasks/{task_id}/submit")
async def submit_task(
    task_id: int,
    request: Request,
    data: TaskSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    is_leader, team_id = await TeamsClient.is_user_team_leader(request)
    if not is_leader:
        raise HTTPException(
            status_code=403, detail="Only team leaders can submit tasks"
        )

    submission = await ZvezdaCRUD.submit_task(
        db,
        task_id=task_id,
        team_id=team_id,
        text_description=data.text_description,
        result_url=data.result_url,
    )
    return {"submission_id": submission.id, "status": submission.status.value}


@router.get("/tasks/{task_id}/submissions", response_model=List[TaskSubmissionRead])
async def get_task_submissions(task_id: int, db: AsyncSession = Depends(get_db)):
    return await ZvezdaCRUD.get_task_submissions(db, task_id)