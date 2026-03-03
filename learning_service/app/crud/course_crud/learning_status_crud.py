from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from db.models.course import Course
from db.models.user_progress import UserProgress


class LearningStatusCRUD:
    async def check_user_completed_all_courses(
        self, db: AsyncSession, user_id: int
    ) -> bool:
        total_courses_result = await db.execute(
            select(func.count()).select_from(Course)
        )
        total_courses = total_courses_result.scalar()

        if total_courses == 0:
            return False

        completed_courses_result = await db.execute(
            select(func.count())
            .select_from(UserProgress)
            .where(UserProgress.user_id == user_id, UserProgress.is_completed == True)
        )
        completed_courses = completed_courses_result.scalar()

        return completed_courses >= total_courses


learning_status_crud = LearningStatusCRUD()
