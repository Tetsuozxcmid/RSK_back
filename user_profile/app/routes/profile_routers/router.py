import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import (
    BulkUpdateLearningRequest,
    ProfileCreateSchema,
    ProfileResponse,
    ProfileUpdate,
    ProfileJoinedTeamUpdate,
    ProfileJoinedOrg,
    UpdateLearningStatusRequest,
    UserRoleAdmin,
    UserRoleUpdate,
    UserRoleUpdateForUser,  
    UserRoleAdmin, 
)
from schemas.user_batch import UserBatchRequest
from db.models.user import User
from db.session import get_db
from cruds.profile_crud import ProfileCRUD
from services.grabber import get_current_user
from services.rabbitmq import get_rabbitmq_connection, publish_role_update
from aio_pika.abc import AbstractRobustConnection
from services.auth_client import get_admin


router = APIRouter(prefix="/profile_interaction")

profile_management_router = APIRouter(tags=["Profile Management"])
profile_batch_router = APIRouter(tags=["Batch Operations"])
profile_admin_router = APIRouter(tags=["Admin Profile Operations"])


@profile_management_router.get("/get_my_profile/", response_model=ProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)
):
    return await ProfileCRUD.get_my_profile(db, user_id)


@profile_management_router.post("/update_user_profile_joined_team/")
async def update_user_profile_joined_team(
    update_data: ProfileJoinedTeamUpdate, db: AsyncSession = Depends(get_db)
):
    logging.info(f" Updating team for user {update_data.user_id}: {update_data}")
    return await ProfileCRUD.update_profile_joined_team(
        db=db,
        user_id=update_data.user_id,
        team_name=update_data.team,
        team_id=update_data.team_id,
    )


@router.post("/update_learning_status/")
async def update_learning_status(
    request: UpdateLearningStatusRequest, db: AsyncSession = Depends(get_db)
):
    user = await db.execute(select(User).where(User.id == request.user_id))
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_learned = request.is_learned
    await db.commit()

    return {
        "status": "success",
        "user_id": request.user_id,
        "is_learned": request.is_learned,
    }


@router.post("/bulk_update_learning/")
async def bulk_update_learning(
    request: BulkUpdateLearningRequest, db: AsyncSession = Depends(get_db)
):
    updated = 0
    for user_data in request.users:
        result = await db.execute(
            update(User)
            .where(User.id == user_data["user_id"])
            .values(is_learned=user_data["is_learned"])
        )
        if result.rowcount > 0:
            updated += 1

    await db.commit()
    return {"status": "success", "updated": updated}


@profile_management_router.post("/update_user_profile_joined_org/")
async def update_user_profile_joined_org(
    update_data: ProfileJoinedOrg, db: AsyncSession = Depends(get_db)
):
    logging.info(f" Updating org for user {update_data.user_id}: {update_data}")
    return await ProfileCRUD.update_profile_joined_org(
        db=db,
        user_id=update_data.user_id,
        organization_name=update_data.Organization,
        organization_id=update_data.Organization_id,
    )


@profile_management_router.patch("/my-role")
async def update_my_role(
    role_data: UserRoleUpdateForUser,
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection),
    user_id: int = Depends(get_current_user),
):
    user, old_role = await ProfileCRUD.update_my_role(
        db=db, user_id=user_id, new_role=role_data.role
    )

    try:
        await publish_role_update(
            rabbitmq,
            user_id=user_id,
            new_role=role_data.role.value,
            old_role=old_role.value if old_role else None,
        )
    except Exception as e:
        print(f"Failed to publish role update: {e}")

    return {
        "message": "Role updated successfully",
        "user_id": user_id,
        "old_role": old_role.value if old_role else None,
        "new_role": role_data.role.value,
    }

@profile_management_router.patch("/admin-role")
async def update_role(
    role_data: UserRoleAdmin,
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection),
    user_id: int = Depends(get_current_user),
    _: str = Depends(get_admin)  
):
    user, old_role = await ProfileCRUD.update_user_role(  
        db=db, user_id=user_id, new_role=role_data.role
    )

    try:
        await publish_role_update(
            rabbitmq,
            user_id=user_id,
            new_role=role_data.role.value,
            old_role=old_role.value if old_role else None,
        )
    except Exception as e:
        print(f"Failed to publish role update: {e}")

    return {
        "message": "Role updated successfully",
        "user_id": user_id,
        "old_role": old_role.value if old_role else None,
        "new_role": role_data.role.value,
    }


@profile_management_router.patch("/update_my_profile/")
async def update_my_profile(
    update_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await ProfileCRUD.update_my_profile(db, update_data, user_id)


@profile_batch_router.post("/get_users_batch")
async def get_users_batch(
    batch_request: UserBatchRequest, db: AsyncSession = Depends(get_db)
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
                "Region": user.Region,
                "Type": user.Type.value if user.Type else None,
            }

        return users_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@profile_admin_router.post("/create_profile/")
async def create_profile(
    profile_data: ProfileCreateSchema, db: AsyncSession = Depends(get_db)
):
    user = await ProfileCRUD.create_profile(db, profile_data)
    return {
        "message": "successfully",
    }


@profile_admin_router.get("/get_profile/")
async def get_profiles(db: AsyncSession = Depends(get_db)):
    users = await ProfileCRUD.get_all_users_profiles(db)
    return users


@profile_admin_router.post("/update_profile/")
async def update_profile(
    update_data: ProfileUpdate, db: AsyncSession = Depends(get_db)
):
    user = await ProfileCRUD.update_profile(update_data, db)
    return {"message": "success"}


@profile_admin_router.get("/by-org/{org_id}")
async def get_users_by_org(
    org_id: int,
    db: AsyncSession = Depends(get_db),
):
    res = await ProfileCRUD.get_users_by_org_id(db=db, org_id=org_id)
    return res


@profile_admin_router.get("/members-count")
async def get_members_count(
    org_ids: list[int] = Query(...),
    db: AsyncSession = Depends(get_db),
):
    counts = await ProfileCRUD.get_member_count_by_id(db=db, org_ids=org_ids)
    return counts


router.include_router(profile_management_router)
router.include_router(profile_batch_router)
router.include_router(profile_admin_router)
