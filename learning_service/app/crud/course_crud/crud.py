from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.course import Course
from typing import List, Optional


class CourseCRUD:
    
    async def get_courses(self, db: AsyncSession) -> List[Course]:
        result = await db.execute(select(Course).limit(10))
        return result.scalars().all()


course_crud = CourseCRUD()

