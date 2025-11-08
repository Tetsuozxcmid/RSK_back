from db.models.submission import Submission
from db.models.user_progress import UserProgress
from db.models.enums.submission_enum import SubmissionStatus
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.course import Course
from typing import List, Optional


class CourseCRUD:
    
    async def get_courses(self, db: AsyncSession) -> List[Course]:
        result = await db.execute(select(Course).limit(10))
        return result.scalars().all()
    
    async def get_course_by_id(self, db: AsyncSession, course_id: int) -> Optional[Course]:
        result = await db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()
    
    async def get_courses_with_progress(self, db: AsyncSession, user_id: int) -> List[Course]:
        
        result = await db.execute(select(Course))
        courses = result.scalars().all()
        
        
        progress_result = await db.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        user_progress = {progress.course_id: progress for progress in progress_result.scalars().all()}
        
        
        submissions_result = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.status == SubmissionStatus.PENDING
            )
        )
        pending_submissions = {submission.course_id for submission in submissions_result.scalars().all()}
        
        
        for course in courses:
            progress = user_progress.get(course.id)
            if progress and progress.is_completed:
                course.is_completed = "true"
            elif course.id in pending_submissions:
                course.is_completed = "process"
            else:
                course.is_completed = "false"
        
        return courses
    
    async def get_course_with_progress(self, db: AsyncSession, course_id: int, user_id: int) -> Optional[Course]:
        
        result = await db.execute(select(Course).where(Course.id == course_id))
        course = result.scalar_one_or_none()
        
        if not course:
            return None
        
        
        progress_result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.course_id == course_id
            )
        )
        progress = progress_result.scalar_one_or_none()
        
        
        submission_result = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.course_id == course_id,
                Submission.status == SubmissionStatus.PENDING
            )
        )
        has_pending_submission = submission_result.scalar_one_or_none() is not None
        
        
        if progress and progress.is_completed:
            course.is_completed = "true"
        elif has_pending_submission:
            course.is_completed = "process"
        else:
            course.is_completed = "false"
        
        return course
    
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

