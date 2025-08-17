
from fastapi import APIRouter,HTTPException,Response,status,Depends

from schemas.user import ProfileCreateSchema, ProfileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.session import get_db
from cruds.profile_crud import ProfileCRUD
from db.models.user import User
from schemas.user import ProfileUpdate
from services.grabber import get_current_user

from fastapi import APIRouter,Depends



from db.session import get_db

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/profile_interaction',tags=['ProfileSystem'])

@router.get('/get_my_profile/', response_model=ProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return await ProfileCRUD.get_my_profile(db, user_id)

@router.patch("/update_my_profile/")
async def update_my_profile(
    update_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return await ProfileCRUD.update_my_profile(db, update_data, user_id)


@router.post('/create_profile/')
async def create_profile(profile_data: ProfileCreateSchema, db: AsyncSession = Depends(get_db)):
    user = await ProfileCRUD.create_profile(db, profile_data)
    return {
        "message": "successfully",
        
    }

@router.get("/get_profile/")
async def get_profiles(db: AsyncSession = Depends(get_db)):
    users = await ProfileCRUD.get_all_users_profiles(db)
    return users

@router.post('/update_profile/')
async def update_profile(update_data: ProfileUpdate,db:AsyncSession = Depends(get_db)):
    user = await ProfileCRUD.update_profile(update_data, db)
    return {
        "message" : "succes"
    }