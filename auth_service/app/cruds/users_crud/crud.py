import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User, UserRole
from routes.users_router.auth_logic import pass_settings
from schemas.user_schemas.user_get import UserOut
from fastapi import HTTPException


class UserCRUD:
    @staticmethod
    async def create_user(db: AsyncSession, user_data):
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email.lower())
        )
        existing_user = existing_user.scalar_one_or_none()
        user_role = user_data.role if hasattr(user_data, "role") else UserRole.STUDENT

        if existing_user and existing_user.verified:
            raise HTTPException(
                status_code=400, detail="User with this email already registered"
            )

        if existing_user and not existing_user.verified:
            await db.delete(existing_user)
            await db.commit()

        confirmation_token = str(uuid.uuid4())

        new_user = User(
            name="",
            email=user_data.email.lower(),
            hashed_password="",
            login=None,
            role=user_role,
            verified=False,
            confirmation_token=confirmation_token,
            auth_provider=None,
            provider_id=None,
            temp_name=user_data.name if user_data.name else "",
            temp_password=pass_settings.get_password_hash(
                user_data.password.get_secret_value()
            ),
            temp_role=user_role,
            temp_login=None,
        )

        db.add(new_user)

        try:
            await db.commit()
            await db.refresh(new_user)

            temp_login = f"user{new_user.id}"
            new_user.temp_login = temp_login
            await db.commit()
            await db.refresh(new_user)

            return new_user, confirmation_token, temp_login
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while registering user: {str(e)}"
            )

    async def create_oauth_user(
        db: AsyncSession,
        name: str,
        provider: str,
        provider_id: str,
        email: str = None,  
        role: UserRole = UserRole.STUDENT,
    ):
        result = await db.execute(
            select(User).where(
                (User.provider_id == provider_id) & (User.auth_provider == provider)
            )
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            return existing_user, False 

        new_user = User(
            name=name,
            email=email.lower() if email else None,
            hashed_password="",
            login=None,
            role=role,
            verified=True,
            auth_provider=provider,
            provider_id=str(provider_id),
        )

        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user, True  
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error creating OAuth user: {str(e)}"
            )

    @staticmethod
    async def confirm_user_email(db: AsyncSession, token: str):
        result = await db.execute(select(User).where(User.confirmation_token == token))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Invalid confirmation token")

        if user.verified:
            raise HTTPException(status_code=400, detail="Email already confirmed")

        user.name = user.temp_name
        user.hashed_password = user.temp_password
        user.role = user.temp_role
        user.login = user.temp_login

        user.temp_name = None
        user.temp_password = None
        user.temp_role = None
        user.temp_login = None

        user.verified = True
        user.confirmation_token = None

        try:
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error confirming email: {str(e)}"
            )

    async def get_all_users(db: AsyncSession):
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()

            if not users:
                return []

            return [UserOut.from_orm(User) for User in users]
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error while fetching users: {str(e)}"
            )

    async def delete_user(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        try:
            await db.delete(user)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while deleting user: {str(e)}"
            )

    async def change_user_password(
        db: AsyncSession, user_id: int, old_password: str, new_password: str
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not pass_settings.verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password")

        new_hashed_password = pass_settings.get_password_hash(new_password)
        user.hashed_password = new_hashed_password

        try:
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"{str(e)}")

    async def get_user_by_id(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"name": user.name, "email": user.email, "role": user.role}
