from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.course import Course
from typing import List, Optional


class CourseCRUD:
    
    async def get_courses(self, db: AsyncSession) -> List[Course]:
        result = await db.execute(select(Course).limit(10))
        return result.scalars().all()
    
    async def update_course_status(self, db: AsyncSession, course_id: int, is_completed: bool) -> Optional[Course]:
        result = await db.execute(select(Course).where(Course.id == course_id))
        course = result.scalar_one_or_none()
        
        if not course:
            return None
        
        course.is_completed = is_completed
        await db.commit()
        await db.refresh(course)
        return course


course_crud = CourseCRUD()

