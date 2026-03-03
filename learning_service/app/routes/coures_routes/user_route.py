from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.course import UserProfileResponse
from db.session import get_db
from services.grabber import get_current_user
from crud.course_crud.learning_status_crud import learning_status_crud
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=UserProfileResponse)
async def get_user_profile(
    db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)
):
    learning = await learning_status_crud.check_user_completed_all_courses(db, user_id)

    return UserProfileResponse(user_id=user_id, learning=learning)
