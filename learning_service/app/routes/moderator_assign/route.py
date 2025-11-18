from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from crud.submission_crud.crud import submission_crud
from schemas.submission import  SubmissionResponse, SubmissionReview
from services.auth_client import get_moderator
from services.assignement import assignment_service
from typing import List

router = APIRouter(tags=["moderator-assignments"])

@router.get("/tasks", response_model=List[SubmissionResponse])
async def get_moderator_tasks(
    db: AsyncSession = Depends(get_db),
    moderator_id: int = Depends(get_moderator)
):

    assigned_ids = await assignment_service.assign_submissions_to_moderator(db, moderator_id)
    
    if not assigned_ids:
        return []
    

    tasks = await submission_crud.get_submissions_by_ids(db, assigned_ids)
    
    return tasks

@router.get("/my-assignments", response_model=List[SubmissionResponse])
async def get_my_current_assignments(
    db: AsyncSession = Depends(get_db),
    moderator_id: int = Depends(get_moderator)
):

    assigned_ids = await assignment_service.get_moderator_assignments(moderator_id)
    
    if not assigned_ids:
        return []
    
    tasks = await submission_crud.get_submissions_by_ids(db, assigned_ids)
    return tasks

@router.patch("/{submission_id}/review", response_model=SubmissionResponse)
async def review_assigned_submission(
    submission_id: int,
    review: SubmissionReview,
    db: AsyncSession = Depends(get_db),
    moderator_id: int = Depends(get_moderator)
):
   
    assigned_ids = await assignment_service.get_moderator_assignments(moderator_id)
    
    if submission_id not in assigned_ids:
        raise HTTPException(
            status_code=403, 
            detail="This submission is not assigned to you or assignment expired"
        )
    
    submission = await submission_crud.review_submission(
        db, submission_id, review.status, description=review.description
    )
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission

@router.post("/release-assignments")
async def release_my_assignments(
    moderator_id: int = Depends(get_moderator)
):

    await assignment_service.release_moderator_assignments(moderator_id)
    return {"message": "Assignments released successfully"}