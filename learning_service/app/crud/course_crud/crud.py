from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.course import Course
from typing import List, Optional


class CourseCRUD:
    
    async def get_courses(self, db: AsyncSession) -> List[Course]:
        result = await db.execute(select(Course).limit(10))
        return result.scalars().all()
    
    async def create_course(self, db: AsyncSession, course_data: dict) -> Course:
        course = Course(
            lesson_name=course_data["lesson_name"],
            lesson_number=course_data["lesson_number"],
            description=course_data.get("description"),
            file_extension=course_data["file_extension"],
            download_url=course_data["download_url"]
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course
    
    async def update_course(self, db: AsyncSession, course_id: int, update_data: dict) -> Optional[Course]:
        course = await self.get_course_by_id(db, course_id)
        if not course:
            return None
        
        for field, value in update_data.items():
            if value is not None:
                setattr(course, field, value)
        
        await db.commit()
        await db.refresh(course)
        return course
    
    async def delete_course(self, db: AsyncSession, course_id: int) -> bool:
        course = await self.get_course_by_id(db, course_id)
        if not course:
            return False
        
        await db.delete(course)
        await db.commit()
        return True


course_crud = CourseCRUD()

