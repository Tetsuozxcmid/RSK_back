from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.submission import Submission, SubmissionStatus
from typing import List, Optional


class SubmissionCRUD:
    
    async def create_submission(self, db: AsyncSession, user_id: int, course_id: int, file_url: str) -> Submission:

        existing_submission = await db.execute(select(Submission).where(Submission.user_id == user_id,Submission.course_id == course_id,Submission.status !=  SubmissionStatus.REJECTED))
        existing = existing_submission.scalar_one_or_none()

        if existing:
            if existing.status == SubmissionStatus.PENDING:
                raise ValueError("Submission already exists and is pending review")
            elif existing.status == SubmissionStatus.APPROVED:
                raise ValueError("Submission already exists and is approved")

        submission = Submission(user_id=user_id, course_id=course_id, file_url=file_url)
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission
    
    async def get_pending_submissions(self, db: AsyncSession) -> List[Submission]:
        result = await db.execute(
            select(Submission).where(Submission.status == SubmissionStatus.PENDING)
        )
        return result.scalars().all()
    
    async def review_submission(self, db: AsyncSession, submission_id: int, status: SubmissionStatus) -> Optional[Submission]:
        result = await db.execute(select(Submission).where(Submission.id == submission_id))
        submission = result.scalar_one_or_none()
        
        if not submission:
            return None
        
        submission.status = status
        await db.commit()
        await db.refresh(submission)
        return submission
    

    async def get_user_submissions(self, db: AsyncSession, user_id: int) -> List[Submission]:
        result = await db.execute(
            select(Submission).where(Submission.user_id == user_id)
        )
        return result.scalars().all()

    async def get_user_submission_by_course(self, db: AsyncSession, user_id: int, course_id: int) -> Optional[Submission]:
        result = await db.execute(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.course_id == course_id
            )
        )
        return result.scalar_one_or_none()


submission_crud = SubmissionCRUD()