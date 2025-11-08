from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from crud.course_crud.crud import course_crud
from crud.user_progress_crud.crud import user_progress_crud
from schemas.course import CourseResponse, CourseCreate, CourseUpdate
from schemas.user_progress import UserProgressUpdate, UserProgressResponse
from services.grabber import get_current_user
from typing import List

router = APIRouter(tags=["courses"])


@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)  
):
    return await course_crud.get_courses_with_progress(db, user_id)

  
@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int, 
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)  
):
    course = await course_crud.get_course_with_progress(db, course_id, user_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db)
     
):

    return await course_crud.create_course(db, course_data.dict())


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: AsyncSession = Depends(get_db)
    
):
    course = await course_crud.update_course(db, course_id, course_update.dict(exclude_unset=True))
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    success = await course_crud.delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")


@router.patch("/{course_id}/progress", response_model=UserProgressResponse)
async def update_course_progress(
    course_id: int,
    progress_update: UserProgressUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return await user_progress_crud.update_progress(db, user_id, course_id, progress_update.is_completed)

