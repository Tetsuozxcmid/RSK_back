from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from db.models.projects import Project, Task, TaskSubmission, TaskStatus
from schemas.proj import CategoryEnum
from services.converter import map_category_label


class ZvezdaCRUD:

    @staticmethod
    async def create_project(db: AsyncSession, project_data):
        project = Project(
            title=project_data.title,
            description=project_data.description,
            organization_name=project_data.organization_name,
            star_index=project_data.star_index,
            star_category=project_data.star_category.value,  # Enum → строка
            level_number=project_data.level_number
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # подгружаем связанные tasks сразу
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project.id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_project(db: AsyncSession, project_id: int):
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @staticmethod
    async def list_projects(db: AsyncSession, organization_name: str = None):
        query = select(Project).options(selectinload(Project.tasks))
        if organization_name:
            query = query.where(Project.organization_name == organization_name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_task(db: AsyncSession, task_id: int):
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @staticmethod
    async def start_task(db: AsyncSession, task_id: int, team_id: int, leader_id: int):
        task = await ZvezdaCRUD.get_task(db, task_id)
        if task.team_id is not None:
            raise HTTPException(status_code=400, detail="Task already taken by another team")

        task.team_id = team_id
        task.leader_id = leader_id
        task.status = TaskStatus.IN_PROGRESS
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def submit_task(db: AsyncSession, task_id: int, team_id: int, text_description: str = None, result_url: str = None):
        task = await ZvezdaCRUD.get_task(db, task_id)
        if task.team_id != team_id:
            raise HTTPException(status_code=403, detail="This team is not assigned to the task")
        if task.status != TaskStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Task is not in progress")

        submission = TaskSubmission(
            task_id=task_id,
            team_id=team_id,
            text_description=text_description,
            result_url=result_url,
            status=TaskStatus.SUBMITTED
        )
        task.status = TaskStatus.SUBMITTED
        db.add(submission)
        db.add(task)
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def get_task_submissions(db: AsyncSession, task_id: int):
        result = await db.execute(select(TaskSubmission).where(TaskSubmission.task_id == task_id))
        return result.scalars().all()


