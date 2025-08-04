from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from fastapi import HTTPException
from schemas.user import ProfileUpdate


class ProfileCRUD:
    @staticmethod
    async def create_profile(db: AsyncSession, profile_data):
        exiting_profile = await db.execute(
            select(User).where(User.NameIRL == profile_data.NameIRL)
        )
        if exiting_profile.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Team already exists")

        new_profile = User(
            NameIRL=profile_data.NameIRL,
            Surname=profile_data.Surname,
            Patronymic=profile_data.Patronymic,
            Description=profile_data.Description,
            Region=profile_data.Region,
            Type=profile_data.Type,
            Organization=profile_data.Organization,
            Organization_id=profile_data.Organization_id,
            team_id=profile_data.team_id,
            team=profile_data.team,
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
