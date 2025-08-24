from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from fastapi import HTTPException
from schemas.user import ProfileResponse, ProfileUpdate


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
            Type=profile_data.Type
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
    async def get_my_profile(db:AsyncSession, user_id: int):
        existing_profile = await db.execute(select(User).where(User.id == user_id))

        profile = existing_profile.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=404, detail="Profile not found"
            )
        return ProfileResponse.model_validate(profile)
    
    @staticmethod
    async def update_my_profile(db: AsyncSession, update_data: ProfileUpdate, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not result:
            raise HTTPException(
                status_code=404, detail="Profile not found"
            )
        
        update_dict = update_data.dict(exclude_unset=True)
        for field in ["NameIRL", "Surname", "Patronymic", "Description", "Region"]:
            if field in update_dict:
                setattr(existing_profile, field, update_dict[field])

        try:
            await db.commit()
            await db.refresh(existing_profile)
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400, detail=f"something got wrong {e}"
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
