from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user_progress import UserProgress
from typing import List, Optional


class UserProgressCRUD:
    async def get_user_progress(
        self, db: AsyncSession, user_id: int, course_id: int
    ) -> Optional[UserProgress]:
        result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id, UserProgress.course_id == course_id
            )
        )
        return result.scalar_one_or_none()

    async def update_progress(
        self, db: AsyncSession, user_id: int, course_id: int, is_completed: bool
    ) -> UserProgress:
        progress = await self.get_user_progress(db, user_id, course_id)

        if not progress:
            progress = UserProgress(
                user_id=user_id, course_id=course_id, is_completed=is_completed
            )
            db.add(progress)
        else:
            progress.is_completed = is_completed

        await db.commit()
        await db.refresh(progress)
        return progress

    async def get_user_progress_list(
        self, db: AsyncSession, user_id: int
    ) -> List[UserProgress]:
        result = await db.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        return result.scalars().all()


user_progress_crud = UserProgressCRUD()
