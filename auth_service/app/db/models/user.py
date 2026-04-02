from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Integer, String, Enum as sqlEnum, or_
from routes.users_router.auth_logic import pass_settings
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MODER = "moder"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    login: Mapped[str] = mapped_column(String(50), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        sqlEnum(UserRole, name="user_role_enum"),
        nullable=True,
        default=UserRole.STUDENT,
    )

    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmation_token: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=True
    )

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    auth_provider: Mapped[str] = mapped_column(String(20), nullable=True)
    provider_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)

    temp_name: Mapped[str] = mapped_column(String(50), nullable=True)
    temp_password: Mapped[str] = mapped_column(String(255), nullable=True)
    temp_role: Mapped[UserRole] = mapped_column(
        sqlEnum(UserRole, name="user_role_enum"), nullable=True
    )
    temp_login: Mapped[str] = mapped_column(String(255), nullable=True)

    @classmethod
    async def check_user(cls, login: str, password: str, db: AsyncSession):
        try:
            print("\n=== DEBUG check_user ===")
            print(f"Login/email provided: {login}")
            print(f"Password length: {len(password)}")

            result = await db.execute(
                select(cls)
                .where(or_(cls.login == login, cls.email == login.lower()))
                .order_by(cls.verified.desc(), cls.id.desc())
            )
            users = list(result.scalars().all())

            if not users:
                print(f"DEBUG: No user found with login/email: {login}")
                return None

            exact_login_users = [user for user in users if user.login == login]
            email_users = [user for user in users if user.email == login.lower()]
            candidates = exact_login_users or email_users or users
            verified_candidates = [user for user in candidates if user.verified]
            user = verified_candidates[0] if verified_candidates else candidates[0]

            if len(users) > 1:
                print(
                    f"WARNING: Multiple auth users found for {login}: {[candidate.id for candidate in users]}. Using user {user.id}"
                )

            print(f"DEBUG: User found - ID: {user.id}, Email: {user.email}")
            print(f"DEBUG: User verified: {user.verified}")
            print(f"DEBUG: Hashed password in DB: {user.hashed_password}")
            print(f"DEBUG: Temp password: {user.temp_password}")

            password_to_check = None

            if user.verified:
                password_to_check = user.hashed_password
                print("DEBUG: Using hashed_password for verified user")
            else:
                password_to_check = user.temp_password
                print("DEBUG: Using temp_password for unverified user")

            if not password_to_check:
                print(f"ERROR: No password hash found for user {user.email}")
                return None

            print("DEBUG: Calling verify_password...")
            is_valid = pass_settings.verify_password(password, password_to_check)
            print(f"DEBUG: Password valid: {is_valid}")

            if is_valid and user.verified:
                return {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
            elif is_valid and not user.verified:
                print(f"DEBUG: User {user.email} is not verified yet")
                return None
            else:
                print(f"DEBUG: Password invalid for user {user.email}")
                return None

        except Exception as e:
            print(f"ERROR in check_user: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return None
