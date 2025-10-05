from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.course_crud.crud import course_crud
from app.crud.user_progress_crud.crud import user_progress_crud
from app.schemas.course import CourseResponse
from app.schemas.user_progress import UserProgressUpdate, UserProgressResponse
from typing import List

router = APIRouter(tags=["courses"])

@router.get("/", response_model=List[CourseResponse])
async def get_courses(db: AsyncSession = Depends(get_db)):
    return await course_crud.get_courses(db)


@router.patch("/{course_id}/progress", response_model=UserProgressResponse)
async def update_course_progress(
    course_id: int,
    user_id: int,
    progress_update: UserProgressUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await user_progress_crud.update_progress(db, user_id, course_id, progress_update.is_completed)