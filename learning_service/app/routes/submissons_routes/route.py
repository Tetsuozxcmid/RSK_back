from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from crud.submission_crud.crud import submission_crud
from schemas.submission import SubmissionCreate, SubmissionResponse, SubmissionReview
from services.grabber import get_current_user
from services.auth_client import get_moderator 
from typing import List

router = APIRouter(tags=["submissions"])

@router.post("/submit", response_model=SubmissionResponse)
async def submit_task(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)  
):
    return await submission_crud.create_submission(
        db, user_id, submission.course_id, submission.file_url
    )

@router.get("/pending", response_model=List[SubmissionResponse])
async def get_pending_submissions(
    db: AsyncSession = Depends(get_db),
    _:str = Depends(get_moderator)
):
    return await submission_crud.get_pending_submissions(db)

@router.patch("/{submission_id}/review", response_model=SubmissionResponse)
async def review_submission(
    submission_id: int,
    review: SubmissionReview,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_moderator)
):
    submission = await submission_crud.review_submission(db, submission_id, review.status, description=review.description)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission

@router.get("/my-submissions", response_model=List[SubmissionResponse])
async def get_my_submissions(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
    _: str = Depends(get_moderator)
):
    return await submission_crud.get_user_submissions(db, user_id)

