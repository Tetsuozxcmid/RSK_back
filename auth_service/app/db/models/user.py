from __future__ import annotations
from typing import List, TYPE_CHECKING
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Integer, String, Enum  as sqlEnum
from routes.users_router.auth_logic import pass_settings
from enum import Enum 
from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True)

    role: Mapped[UserRole] = mapped_column(
    sqlEnum(UserRole, name="user_role_enum"),
    nullable=True, 
    default=UserRole.STUDENT
    )

    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmation_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    auth_provider: Mapped[str] = mapped_column(String(20), nullable=True)
    provider_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)

    @classmethod
    async def check_user(cls, name: str, password: str, db: AsyncSession):
        result = await db.execute(select(cls).where(cls.name == name))
        user = result.scalar_one_or_none()
        if not user or not pass_settings.verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            return None
        
        if not user.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your email for confirmation."
            )

        return {"id": user.id, "name": user.name,"verified":user.verified,"role": user.role.value}
    
    
