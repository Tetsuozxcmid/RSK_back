from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.course_crud.crud import course_crud
from app.schemas.course import CourseResponse, CourseUpdate
from typing import List

router = APIRouter(tags=["courses"])

@router.get("/", response_model=List[CourseResponse])
async def get_courses(db: AsyncSession = Depends(get_db)):
    return await course_crud.get_courses(db)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course_status(
    course_id: int,
    course_update: CourseUpdate,
    db: AsyncSession = Depends(get_db)
):
    course = await course_crud.update_course_status(db, course_id, course_update.is_completed)
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course