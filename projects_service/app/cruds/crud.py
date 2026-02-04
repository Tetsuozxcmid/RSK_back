from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from fastapi import HTTPException, Request

from db.models.projects import Project, Task, TaskSubmission, TaskStatus
from services.teams_client import TeamsClient


class ZvezdaCRUD:
    # === АДМИНИСТРАТИВНЫЕ ФУНКЦИИ (ADMIN) ===

    @staticmethod
    async def create_project(db: AsyncSession, project_data):
        project = Project(
            title=project_data.title,
            description=project_data.description,
            organization_name=project_data.organization_name,
            star_index=project_data.star_index,
            star_category=project_data.star_category.value,
            level_number=project_data.level_number,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # Возвращаем с подгруженными задачами для соответствия схеме
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project.id)
        )
        return result.scalar_one()

    @staticmethod
    async def update_project(db: AsyncSession, project_id: int, project_data):
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Обновляем только присланные поля
        for key, value in project_data.dict(exclude_unset=True).items():
            if key == "star_category":
                setattr(project, key, value.value)
            else:
                setattr(project, key, value)

        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: int):
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        await db.delete(project)
        await db.commit()

    @staticmethod
    async def create_task(db: AsyncSession, task_data, project_id: int):
        task = Task(
            project_id=project_id,
            title=task_data.title,
            description=task_data.description,
            prize_points=task_data.prize_points or 0,
            materials=getattr(task_data, "materials", []) or [],
            status=TaskStatus.NOT_STARTED,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def update_task(db: AsyncSession, task_id: int, task_data):
        task = await db.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        for key, value in task_data.dict(exclude_unset=True).items():
            setattr(task, key, value)

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int):
        task = await db.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await db.delete(task)
        await db.commit()

    # === ФУНКЦИИ МОДЕРАТОРА (MODER) ===

    @staticmethod
    async def get_tasks_for_review(
        db: AsyncSession, moderator_id: int
    ) -> List[TaskSubmission]:
        """
        Выдает 5 заданий на проверку.
        1. Сначала возвращает те, что уже закреплены за этим модером и 10 минут еще не истекли.
        2. Если их меньше 5, добирает новые свободные задания.
        """
        now = datetime.utcnow()
        lock_limit = now - timedelta(minutes=10)

        # 1. Проверяем текущие активные брони модератора
        query_current = select(TaskSubmission).where(
            and_(
                TaskSubmission.moderator_id == moderator_id,
                TaskSubmission.reviewed_at == None,
                TaskSubmission.submitted_at >= lock_limit,
            )
        )
        result = await db.execute(query_current)
        current_tasks = result.scalars().all()

        if len(current_tasks) >= 5:
            return current_tasks[:5]

        # 2. Добираем новые задания (статус SUBMITTED, никем не заняты ИЛИ бронь другого модера истекла)
        needed = 5 - len(current_tasks)
        query_new = (
            select(TaskSubmission)
            .where(
                and_(
                    TaskSubmission.status == TaskStatus.SUBMITTED,
                    or_(
                        TaskSubmission.moderator_id == None,
                        TaskSubmission.submitted_at < lock_limit,
                    ),
                )
            )
            .limit(needed)
        )

        new_res = await db.execute(query_new)
        new_tasks = new_res.scalars().all()

        # Фиксируем время выдачи (submitted_at) и ID модератора
        for sub in new_tasks:
            sub.moderator_id = moderator_id
            sub.submitted_at = (
                now  # Перезаписываем время для отсчета 10 минут модератору
            )
            db.add(sub)

        if new_tasks:
            await db.commit()

        return list(current_tasks) + list(new_tasks)

    @staticmethod
    async def review_submission(
        db: AsyncSession,
        submission_id: int,
        moderator_id: int,
        status: TaskStatus,
        description: Optional[str] = None,
    ):
        """
        Проверка задания. Проверяет права модератора и лимит времени.
        """
        result = await db.execute(
            select(TaskSubmission).where(TaskSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(404, "Submission not found")

        # Проверка: закреплено ли задание за этим модером
        if submission.moderator_id != moderator_id:
            raise HTTPException(
                403, "This task is assigned to another moderator or not locked by you"
            )

        # Проверка: не истекли ли 10 минут
        if submission.submitted_at < (datetime.utcnow() - timedelta(minutes=10)):
            raise HTTPException(
                400, "Lock period (10 min) expired. Please fetch tasks again."
            )

        task = await db.get(Task, submission.task_id)

        if status == TaskStatus.ACCEPTED:
            submission.status = TaskStatus.ACCEPTED
            task.status = TaskStatus.ACCEPTED
            # Здесь в будущем вызов TeamsClient для начисления баллов
        else:
            submission.status = TaskStatus.REJECTED
            task.status = TaskStatus.IN_PROGRESS  # Возвращаем в работу команде

        submission.reviewed_at = datetime.utcnow()
        if description:
            submission.text_description = (
                f"{submission.text_description or ''}\n\nMOD_NOTE: {description}"
            )

        db.add(submission)
        db.add(task)
        await db.commit()
        await db.refresh(submission)
        return submission

    # === ОБЩИЕ ФУНКЦИИ (USERS) ===

    @staticmethod
    async def get_project(db: AsyncSession, project_id: int):
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(404, "Project not found")
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
            raise HTTPException(404, "Task not found")
        return task

    @staticmethod
    async def start_task(
        db: AsyncSession, task_id: int, user_id: int, request: Request
    ):
        is_leader, team_id = await TeamsClient.is_user_team_leader(request)
        if not is_leader:
            raise HTTPException(403, "Only team leaders can take tasks")

        task = await ZvezdaCRUD.get_task(db, task_id)
        if task.team_id is not None:
            raise HTTPException(400, "Task already taken")

        task.team_id = team_id
        task.leader_id = user_id
        task.status = TaskStatus.IN_PROGRESS
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def submit_task(
        db: AsyncSession,
        task_id: int,
        team_id: int,
        text_description: str = None,
        result_url: str = None,
    ):
        task = await ZvezdaCRUD.get_task(db, task_id)

        if task.team_id != team_id:
            raise HTTPException(403, "This team is not assigned to the task")

        submission = TaskSubmission(
            task_id=task_id,
            team_id=team_id,
            text_description=text_description,
            result_url=result_url,
            status=TaskStatus.SUBMITTED,
        )

        task.status = TaskStatus.SUBMITTED
        db.add(submission)
        db.add(task)
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def list_tasks(db: AsyncSession, project_id: int = None):
        query = select(Task)
        if project_id:
            query = query.where(Task.project_id == project_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_task_submissions(db: AsyncSession, task_id: int):
        result = await db.execute(
            select(TaskSubmission).where(TaskSubmission.task_id == task_id)
        )
        return result.scalars().all()
