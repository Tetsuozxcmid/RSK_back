import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from db.models.user_enum import UserEnum
from db.models.user import User
from fastapi import HTTPException
from schemas.user import OrganizationSimple, ProfileResponse, ProfileUpdate
from services.orgs_client import OrgsClient


class ProfileCRUD:
    @staticmethod
    async def create_profile(db: AsyncSession, profile_data):
        exiting_profile = await db.execute(
            select(User).where(User.NameIRL == profile_data.NameIRL)
        )
        if exiting_profile.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Profile already exists")

        new_profile = User(
            NameIRL=profile_data.NameIRL,
            Surname=profile_data.Surname,
            Patronymic=profile_data.Patronymic,
            Description=profile_data.Description,
            Region=profile_data.Region,
            Type=profile_data.Type,
            Organization=profile_data.Organization,
        )

        db.add(new_profile)

        try:
            await db.commit()
            await db.refresh(new_profile)
            return new_profile

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while registering team: {str(e)}"
            )

    @staticmethod
    async def get_my_profile(db: AsyncSession, user_id: int):
        existing_profile = await db.execute(select(User).where(User.id == user_id))
        profile = existing_profile.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        
        organization_info = None
        if profile.Organization_id and profile.Organization_id > 0:
            org_data = await OrgsClient.get_organization_by_id(profile.Organization_id)
            
            if org_data:
                
                organization_info = OrganizationSimple(
                    id=org_data.get("id"),
                    name=org_data.get("short_name") or org_data.get("full_name"),
                    full_name=org_data.get("full_name"),
                    short_name=org_data.get("short_name"),
                    inn=org_data.get("inn"),
                    region=org_data.get("region"),
                    type=org_data.get("type"),
                    
                )
        
        
        profile_data = {
            "NameIRL": profile.NameIRL,
            "email": profile.email,
            "username": profile.username,
            "Surname": profile.Surname,
            "Patronymic": profile.Patronymic,
            "Description": profile.Description,
            "Region": profile.Region,
            "Type": profile.Type,
            "Organization_id": profile.Organization_id,
            "Organization": organization_info,  
            "team": profile.team,
            "team_id": profile.team_id,
            "is_learned": profile.is_learned
        }
        
        return ProfileResponse(**profile_data)

    @staticmethod
    async def update_my_profile(
        db: AsyncSession, update_data: ProfileUpdate, user_id: int
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        update_dict = update_data.dict(exclude_unset=True)

        for field in [
            "NameIRL",
            "Surname",
            "Patronymic",
            "Description",
            "Region",
            "Organization_id",  
            "email",
            "Type",
        ]:
            if field in update_dict:
                setattr(existing_profile, field, update_dict[field])

        try:
            await db.commit()
            await db.refresh(existing_profile)
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"something got wrong {e}")
        
    @staticmethod
    async def update_my_role(
        db: AsyncSession, 
        user_id: int, 
        new_role: UserEnum
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        old_role = user.Type
        user.Type = new_role
        
        try:
            await db.commit()
            await db.refresh(user)
            return user, old_role
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"Error updating role: {str(e)}")

    @staticmethod
    async def get_all_users_profiles(db: AsyncSession):
        result = await db.execute(select(User))
        return result.scalars().all()

    @staticmethod
    async def update_profile(update_data: ProfileUpdate, db: AsyncSession):
        result = await db.execute(select(User).where(User.id == update_data.id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        for field, value in update_data.dict(exclude_unset=True).items():
            if field != "id":
                setattr(existing_profile, field, value)

        try:
            await db.commit()
            await db.refresh(existing_profile)
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while updating profile: {str(e)}"
            )

    @staticmethod
    async def update_profile_joined_team(
        db: AsyncSession, user_id: int, team_name: str, team_id: int
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        existing_profile.team = team_name
        existing_profile.team_id = team_id

        try:
            await db.commit()
            await db.refresh(existing_profile)
            logging.info(f"User {user_id} joined team '{team_name}' (ID: {team_id})")
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while updating profile: {str(e)}"
            )

    @staticmethod
    async def update_profile_joined_org(
        db: AsyncSession, user_id: int, organization_name: str, organization_id: int
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        existing_profile.Organization = organization_name
        existing_profile.Organization_id = organization_id

        try:
            await db.commit()
            await db.refresh(existing_profile)
            logging.info(
                f"User {user_id} team is in org '{organization_name}' (ID: {organization_id})"
            )
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while updating profile: {str(e)}"
            )

    @staticmethod
    async def get_users_by_org_id(db: AsyncSession, org_id: int):
        result = await db.execute(select(User).where(User.Organization_id == org_id))
        return result.scalars().all()

    @staticmethod
    async def get_member_count_by_id(db: AsyncSession, org_ids: list[int]):
        res = await db.execute(
            select(User.Organization_id, func.count(User.id))
            .where(User.Organization_id.in_(org_ids))
            .group_by(User.Organization_id)
        )
        rows = res.all()

        counts = {org_id: 0 for org_id in org_ids}
        for org_id, cnt in rows:
            counts[org_id] = cnt

        return counts
