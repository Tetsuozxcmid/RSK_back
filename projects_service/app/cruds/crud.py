from datetime import datetime, timedelta, timezone

from typing import List, Optional

from fastapi import HTTPException, Request
from sqlalchemy import and_, or_, update, text

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from db.models.projects import Project, Task, TaskSubmission, TaskStatus
from services.teams_client import TeamsClient


class ZvezdaCRUD:
    @staticmethod
    async def create_project(db: AsyncSession, project_data):
        project = Project(
            title=project_data.title,
            description=project_data.description,
            organization_id=project_data.organization_id,
            star_index=project_data.star_index,
            star_category=project_data.star_category.value,
            level_number=project_data.level_number,
        )

        db.add(project)
        await db.commit()
        await db.refresh(project)

        result = await db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project.id)
        )

        return result.scalar_one()

    @staticmethod
    async def list_projects(db: AsyncSession, organization_id: Optional[int] = None):
        query = select(Project).options(selectinload(Project.tasks))

        if organization_id:
            query = query.where(Project.organization_id == organization_id)

        result = await db.execute(query)
        return result.scalars().all()

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
    async def update_project(db: AsyncSession, project_id: int, project_data):
        project = await db.get(Project, project_id)

        if not project:
            raise HTTPException(404, "Project not found")

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
            raise HTTPException(404, "Project not found")

        await db.delete(project)
        await db.commit()

    @staticmethod
    async def create_task(db: AsyncSession, task_data, project_id: int):
        task = Task(
            project_id=project_id,
            title=task_data.title,
            description=task_data.description,
            prize_points=task_data.prize_points or 0,
            materials=task_data.materials or [],
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
            raise HTTPException(404, "Task not found")

        for key, value in task_data.dict(exclude_unset=True).items():
            setattr(task, key, value)

        await db.commit()
        await db.refresh(task)

        return task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int):
        task = await db.get(Task, task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        await db.delete(task)
        await db.commit()

    @staticmethod
    async def list_tasks(db: AsyncSession, project_id: Optional[int] = None):
        query = select(Task)
        if project_id:
            query = query.where(Task.project_id == project_id)
        
        
        query = query.order_by(Task.id)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        
        print(f"\n=== DEBUG list_tasks ===")
        for task in tasks:
            print(f"Task {task.id}: status = {task.status}")
        print("=" * 30)
        
        return tasks

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
            raise HTTPException(403, "Only team leaders can start tasks")

        task = await ZvezdaCRUD.get_task(db, task_id)

        result = await db.execute(
            select(TaskSubmission).where(
                TaskSubmission.task_id == task_id,
                TaskSubmission.team_id == team_id,
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(400, "Your team already started this task")

        submission = TaskSubmission(
            task_id=task_id,
            team_id=team_id,
            status=TaskStatus.IN_PROGRESS,
        )

        db.add(submission)
        
        
        task.status = TaskStatus.IN_PROGRESS
        db.add(task)
        
        await db.commit()
        await db.refresh(submission)

        return submission

    @staticmethod
    async def submit_task(
        db: AsyncSession,
        task_id: int,
        team_id: int,
        text_description: Optional[str],
        result_url: Optional[str],
    ):
        result = await db.execute(
            select(TaskSubmission)
            .options(selectinload(TaskSubmission.task))  
            .where(
                TaskSubmission.task_id == task_id,
                TaskSubmission.team_id == team_id,
            )
        )

        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(403, "Task was not started by this team")

        submission.text_description = text_description
        submission.result_url = result_url
        submission.status = TaskStatus.SUBMITTED
        submission.submitted_at = datetime.now(timezone.utc)

        
        task = submission.task
        if task:
            task.status = TaskStatus.SUBMITTED
            db.add(task)

        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        return submission

    @staticmethod
    async def get_tasks_for_review(db: AsyncSession, moderator_id: int) -> List[dict]:
            now = datetime.now(timezone.utc)
            lock_limit = now - timedelta(minutes=10)
            
            print(f"[DEBUG] Moderator {moderator_id} fetching tasks at {now}")
            
            
            query_current = (
                select(TaskSubmission)
                .options(selectinload(TaskSubmission.task).selectinload(Task.project))
                .where(
                    and_(
                        TaskSubmission.moderator_id == moderator_id,
                        TaskSubmission.reviewed_at == None,  
                        TaskSubmission.submitted_at >= lock_limit,  
                    )
                )
            )

            result = await db.execute(query_current)
            current_tasks = result.scalars().all()
            
            print(f"[DEBUG] Found {len(current_tasks)} current locked tasks")

            
            if len(current_tasks) >= 5:
                return await ZvezdaCRUD._submissions_to_dict(current_tasks[:5])

            
            needed = 5 - len(current_tasks)
            
            print(f"[DEBUG] Need {needed} more tasks")

            
            query_new = (
                select(TaskSubmission)
                .options(selectinload(TaskSubmission.task).selectinload(Task.project))
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
            
            print(f"[DEBUG] Found {len(new_tasks)} new available tasks")

            
            for sub in new_tasks:
                sub.moderator_id = moderator_id
                sub.submitted_at = now  
                db.add(sub)

            if new_tasks:
                await db.commit()
                print(f"[DEBUG] Locked {len(new_tasks)} tasks for moderator {moderator_id}")
                
                
                for sub in new_tasks:
                    await db.refresh(sub)

            
            all_tasks = list(current_tasks) + list(new_tasks)
            return await ZvezdaCRUD._submissions_to_dict(all_tasks)

    @staticmethod
    async def _submissions_to_dict(submissions: List[TaskSubmission]) -> List[dict]:
        result = []
        now = datetime.now(timezone.utc)  
        LOCK_DURATION_MINUTES = 10  

        for sub in submissions:
            if not sub.task or not sub.task.project:
                continue

            project_category = sub.task.project.star_category
            if isinstance(project_category, str):
                from schemas.proj import CATEGORY_MAP
                project_category = CATEGORY_MAP.get(project_category, project_category)

            
            time_left = None
            if sub.moderator_id and sub.submitted_at:
                
                lock_expires_at = sub.submitted_at + timedelta(minutes=LOCK_DURATION_MINUTES)
                
                if now < lock_expires_at:
                   
                    time_left = int((lock_expires_at - now).total_seconds())
                else:
                    
                    time_left = 0

            result.append(
                {
                    "id": sub.id,
                    "task_id": sub.task_id,
                    "team_id": sub.team_id,
                    "text_description": sub.text_description,
                    "result_url": sub.result_url,
                    "submitted_at": sub.submitted_at,
                    "reviewed_at": sub.reviewed_at,
                    "status": sub.status,
                    "moderator_id": sub.moderator_id,
                    "time": time_left,  
                    "project_id": sub.task.project.id,
                    "project_title": sub.task.project.title,
                    "project_category": project_category,
                    "task_title": sub.task.title,
                    "task_description": sub.task.description,
                }
            )

        return result

    @staticmethod
    async def review_submission(
        db: AsyncSession,
        submission_id: int,
        moderator_id: int,
        status: TaskStatus,
        description: Optional[str] = None,
    ):
        now = datetime.now(timezone.utc)
        lock_limit = now - timedelta(minutes=10)
        
        print(f"\n=== DEBUG REVIEW START ===")
        print(f"Submission ID: {submission_id}")
        print(f"New status value: {status.value if hasattr(status, 'value') else status}")

        # Получаем submission с загрузкой связанной задачи
        result = await db.execute(
            select(TaskSubmission)
            .options(selectinload(TaskSubmission.task))
            .where(TaskSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(404, "Submission not found")

        if submission.moderator_id != moderator_id:
            raise HTTPException(403, "This task is assigned to another moderator")

        if submission.submitted_at < lock_limit:
            raise HTTPException(400, "Lock expired. Fetch tasks again.")

        # Обновляем submission
        submission.status = status
        submission.reviewed_at = now

        if description:
            submission.text_description = (
                f"{submission.text_description or ''}\n\nMOD_NOTE: {description}"
            )
        db.add(submission)

        # 👇 ПРЕОБРАЗУЕМ СТАТУС В СТРОКУ ДЛЯ СРАВНЕНИЯ
        status_str = status.value if hasattr(status, 'value') else str(status)
        print(f"📊 Status string for comparison: '{status_str}'")

        if status_str == "ACCEPTED":
            print(f"✅ Status is ACCEPTED, proceeding with task update and points")
            
            # Отдельный запрос для task
            task_result = await db.execute(
                select(Task).where(Task.id == submission.task_id)
            )
            task = task_result.scalar_one_or_none()
            
            if task:
                print(f"🔄 Task {task.id} current status: {task.status}")
                print(f"💰 Task prize points: {task.prize_points}")
                print(f"👥 Team ID: {submission.team_id}")
                
                task.status = TaskStatus.ACCEPTED
                db.add(task)
                print(f"✅ Task {task.id} updated to ACCEPTED")
                
                # 👇 НАЧИСЛЯЕМ ОЧКИ КОМАНДЕ
                team_id = submission.team_id
                points_to_add = task.prize_points
                
                if team_id and points_to_add:
                    print(f"💰 Adding {points_to_add} points to team {team_id}")
                    
                    # Вызываем метод для начисления очков
                    try:
                        success = await TeamsClient.add_points_to_team(
                            team_id=team_id,
                            points=points_to_add
                        )
                        
                        if success:
                            print(f"✅ Points added successfully to team {team_id}")
                        else:
                            print(f"❌ Failed to add points to team {team_id}")
                    except Exception as e:
                        print(f"❌ Exception while adding points: {str(e)}")
                else:
                    print(f"❌ Cannot add points: team_id={team_id}, points={points_to_add}")
            else:
                print(f"❌ Task {submission.task_id} not found")
        else:
            print(f"❌ Status is '{status_str}', not ACCEPTED")

        # ОДИН КОММИТ ДЛЯ ВСЕГО
        await db.commit()
        print(f"✅ Changes committed to database")
        
        # Проверяем статус задачи после коммита
        final_check = await db.execute(
            select(Task).where(Task.id == submission.task_id)
        )
        final_task = final_check.scalar_one()
        print(f"✅ FINAL CHECK: task {final_task.id} status = {final_task.status}")

        return submission
