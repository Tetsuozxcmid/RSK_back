import uuid
from sqlalchemy import or_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User, UserRole
from routes.users_router.auth_logic import pass_settings
from schemas.user_schemas.user_get import UserOut
from fastapi import HTTPException
from services.oauth_profile import build_full_name, clean_text


def _normalize_text(value: str | None) -> str:
    return clean_text(value)


def _truncate_text(value: str | None, max_length: int) -> str:
    normalized = _normalize_text(value)
    if len(normalized) <= max_length:
        return normalized
    return normalized[:max_length].rstrip()


def _resolve_registration_names(user_data) -> tuple[str, str, str]:
    first_name = _normalize_text(getattr(user_data, "first_name", None))
    last_name = _normalize_text(getattr(user_data, "last_name", None))
    raw_name = _normalize_text(getattr(user_data, "name", None))

    if first_name or last_name:
        return first_name, last_name, build_full_name(first_name, last_name)

    if not raw_name:
        return "", "", ""

    raw_parts = [part for part in raw_name.split() if part]
    if len(raw_parts) >= 2:
        first_name = raw_parts[0]
        last_name = " ".join(raw_parts[1:]).strip()

    return first_name or raw_name, last_name, raw_name


def _default_login_for_user_id(user_id: int) -> str:
    return f"user{user_id}"


class UserCRUD:
    @staticmethod
    async def create_user(db: AsyncSession, user_data):
        normalized_email = user_data.email.lower()
        existing_user = await db.execute(
            select(User).where(User.email == normalized_email)
        )
        existing_user = existing_user.scalar_one_or_none()
        user_role = user_data.role if hasattr(user_data, "role") else UserRole.STUDENT
        _, _, full_name = _resolve_registration_names(user_data)

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
            email=normalized_email,
            hashed_password="",
            login=None,
            role=user_role,
            verified=False,
            confirmation_token=confirmation_token,
            auth_provider=None,
            provider_id=None,
            temp_name=_truncate_text(full_name, 50),
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

            temp_login = _default_login_for_user_id(new_user.id)
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
            should_update = False

            normalized_email = email.lower() if email else None
            normalized_name = str(name or "").strip()
            normalized_login = _default_login_for_user_id(existing_user.id)

            if normalized_email and not existing_user.email:
                existing_user.email = normalized_email
                should_update = True

            if normalized_name and not str(existing_user.name or "").strip():
                existing_user.name = _truncate_text(normalized_name, 50)
                should_update = True

            if not _normalize_text(existing_user.login):
                existing_user.login = normalized_login
                should_update = True

            if should_update:
                try:
                    await db.commit()
                    await db.refresh(existing_user)
                except Exception as e:
                    await db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error updating OAuth user: {str(e)}",
                    )

            return existing_user, False

        new_user = User(
            name=_truncate_text(name, 50),
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

            if not _normalize_text(new_user.login):
                new_user.login = _default_login_for_user_id(new_user.id)
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

    @staticmethod
    async def get_all_users(db: AsyncSession):
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()

            if not users:
                return []

            users_list = []
            for user in users:
                users_list.append(
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "verified": user.verified,
                        "role": user.role.value
                        if hasattr(user.role, "value")
                        else str(user.role),
                    }
                )

            return users_list

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

    @staticmethod
    async def reset_password_by_email_or_login(
        db: AsyncSession, email_or_login: str, new_password: str
    ):
        result = await db.execute(
            select(User)
            .where(
                or_(User.email == email_or_login.lower(), User.login == email_or_login)
            )
            .order_by(User.verified.desc())
        )
        users = result.scalars().all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail=f"User with email/login '{email_or_login}' not found",
            )

        user = next((u for u in users if u.verified), users[0])

        verified_users = [u for u in users if u.verified]
        if len(verified_users) > 1:
            print(
                f"WARNING: Multiple verified users found for {email_or_login}: {[u.id for u in verified_users]}"
            )

            user = verified_users[0]

        if not user.verified:
            raise HTTPException(
                status_code=400,
                detail="User is not verified. Please confirm email first.",
            )

        new_hashed_password = pass_settings.get_password_hash(new_password)

        user.hashed_password = new_hashed_password

        try:
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error resetting password: {str(e)}"
            )
