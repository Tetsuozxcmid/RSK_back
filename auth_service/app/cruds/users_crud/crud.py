import uuid
from sqlalchemy import or_, text
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


def _normalize_email(value: str | None) -> str:
    return _normalize_text(value).lower()


def _has_text(value: str | None) -> bool:
    return bool(_normalize_text(value))


def _user_priority(user: User) -> tuple[int, int, int, int, int]:
    return (
        1 if user.verified else 0,
        1 if _has_text(user.login) else 0,
        1 if _has_text(user.name) else 0,
        1 if _has_text(user.auth_provider) else 0,
        int(user.id or 0),
    )


def _select_primary_user(users: list[User]) -> User | None:
    if not users:
        return None
    return max(users, key=_user_priority)


class UserCRUD:
    @staticmethod
    async def _lock_email(db: AsyncSession, normalized_email: str) -> None:
        if not normalized_email:
            return

        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"auth-users-email:{normalized_email}"},
        )

    @staticmethod
    async def get_users_by_email(db: AsyncSession, email: str | None) -> list[User]:
        normalized_email = _normalize_email(email)
        if not normalized_email:
            return []

        result = await db.execute(
            select(User)
            .where(User.email == normalized_email)
            .order_by(User.verified.desc(), User.id.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def select_primary_user(users: list[User]) -> User | None:
        return _select_primary_user(users)

    @staticmethod
    def _sync_oauth_fields(
        user: User,
        *,
        name: str,
        provider: str,
        provider_id: str,
        email: str | None,
    ) -> bool:
        should_update = False
        normalized_email = _normalize_email(email)
        normalized_name = _truncate_text(name, 50)

        if normalized_email and not _has_text(user.email):
            user.email = normalized_email
            should_update = True

        if not _has_text(user.name):
            promoted_name = _truncate_text(user.temp_name, 50) if _has_text(user.temp_name) else normalized_name
            if promoted_name:
                user.name = promoted_name
                should_update = True

        if not _has_text(user.login):
            promoted_login = _normalize_text(user.temp_login) or _default_login_for_user_id(user.id)
            user.login = promoted_login
            should_update = True

        if not user.verified:
            if _has_text(user.temp_password):
                user.hashed_password = user.temp_password
            if user.temp_role is not None:
                user.role = user.temp_role

            user.temp_name = None
            user.temp_password = None
            user.temp_role = None
            user.temp_login = None
            user.verified = True
            user.confirmation_token = None
            should_update = True

        if normalized_name and not _has_text(user.name):
            user.name = normalized_name
            should_update = True

        normalized_provider_id = str(provider_id)
        if not _has_text(user.auth_provider):
            user.auth_provider = provider
            user.provider_id = normalized_provider_id
            should_update = True
        elif user.auth_provider == provider and not _has_text(user.provider_id):
            user.provider_id = normalized_provider_id
            should_update = True

        return should_update

    @staticmethod
    async def create_user(db: AsyncSession, user_data):
        normalized_email = _normalize_email(user_data.email)
        await UserCRUD._lock_email(db, normalized_email)

        existing_users = await UserCRUD.get_users_by_email(db, normalized_email)
        user_role = user_data.role if hasattr(user_data, "role") else UserRole.STUDENT
        _, _, full_name = _resolve_registration_names(user_data)

        if any(user.verified for user in existing_users):
            raise HTTPException(
                status_code=400,
                detail="Пользователь с этой электронной почтой уже зарегистрирован",
            )

        for existing_user in existing_users:
            await db.delete(existing_user)

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

    @staticmethod
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
            should_update = UserCRUD._sync_oauth_fields(
                existing_user,
                name=name,
                provider=provider,
                provider_id=str(provider_id),
                email=email,
            )

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

        normalized_email = _normalize_email(email)
        if normalized_email:
            await UserCRUD._lock_email(db, normalized_email)
            existing_email_users = await UserCRUD.get_users_by_email(db, normalized_email)
            if existing_email_users:
                primary_user = UserCRUD.select_primary_user(existing_email_users)
                if primary_user is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Error resolving OAuth user by email",
                    )

                duplicate_users = [
                    user
                    for user in existing_email_users
                    if user.id != primary_user.id and not user.verified
                ]
                for duplicate_user in duplicate_users:
                    await db.delete(duplicate_user)

                should_update = UserCRUD._sync_oauth_fields(
                    primary_user,
                    name=name,
                    provider=provider,
                    provider_id=str(provider_id),
                    email=normalized_email,
                )

                if should_update or duplicate_users:
                    try:
                        await db.commit()
                        await db.refresh(primary_user)
                    except Exception as e:
                        await db.rollback()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Error updating OAuth user by email: {str(e)}",
                        )

                return primary_user, False

        new_user = User(
            name=_truncate_text(name, 50),
            email=normalized_email or None,
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
