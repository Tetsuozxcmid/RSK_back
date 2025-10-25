import logging
from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import ProfileCreateSchema, ProfileResponse, ProfileUpdate, ProfileJoinedTeamUpdate
from schemas.user_batch import UserBatchRequest
from db.models.user import User
from db.session import get_db
from cruds.profile_crud import ProfileCRUD
from services.grabber import get_current_user
from services.parser import org_parser
import json

router = APIRouter(prefix='/profile_interaction')

profile_management_router = APIRouter(tags=["Profile Management"])
profile_batch_router = APIRouter(tags=["Batch Operations"])
profile_admin_router = APIRouter(tags=["Admin Profile Operations"])

@profile_management_router.get('/get_my_profile/', response_model=ProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return await ProfileCRUD.get_my_profile(db, user_id)

@profile_management_router.post('/update_user_profile_joined_team/')
async def update_user_profile_joined_team(
    update_data: ProfileJoinedTeamUpdate,  
    db: AsyncSession = Depends(get_db)
):
    
    logging.info(f" Updating team for user {update_data.user_id}: {update_data}")
    return await ProfileCRUD.update_profile_joined_team(
        db=db, 
        user_id=update_data.user_id,  
        team_name=update_data.team,
        team_id=update_data.team_id
    )

@profile_management_router.patch("/update_my_profile/")
async def update_my_profile(
    update_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)):

    return await ProfileCRUD.update_my_profile(db, update_data, user_id)

@profile_management_router.get("/get_orgs/")
async def get_orgs(skip: int = 0,limit: int = 50,search: str = None):
    return org_parser.get_organizations(skip=skip,limit=limit,search=search)

@profile_batch_router.post("/get_users_batch")
async def get_users_batch(
    batch_request: UserBatchRequest,  
    db: AsyncSession = Depends(get_db)
):
    try:
        if not batch_request.user_ids:
            return {}
        
        result = await db.execute(
            select(User).where(User.id.in_(batch_request.user_ids))
        )
        users = result.scalars().all()
        
        users_data = {}
        for user in users:
            users_data[user.id] = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "NameIRL": user.NameIRL,
                "Surname": user.Surname,
                "Patronymic": user.Patronymic,
                "Region": user.Region
            }
        
        return users_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@profile_admin_router.post('/create_profile/')
async def create_profile(profile_data: ProfileCreateSchema, db: AsyncSession = Depends(get_db)):
    user = await ProfileCRUD.create_profile(db, profile_data)
    return {
        "message": "successfully",
    }

@profile_admin_router.get("/get_profile/")
async def get_profiles(db: AsyncSession = Depends(get_db)):
    users = await ProfileCRUD.get_all_users_profiles(db)
    return users

@profile_admin_router.post('/update_profile/')
async def update_profile(update_data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    user = await ProfileCRUD.update_profile(update_data, db)
    return {
        "message": "success"
    }

router.include_router(profile_management_router)
router.include_router(profile_batch_router)
router.include_router(profile_admin_router)
