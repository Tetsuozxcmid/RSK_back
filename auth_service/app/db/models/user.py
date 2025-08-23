from __future__ import annotations
from typing import List,TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.base import Base
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,String
from routes.users_router.auth_logic import pass_settings

from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    name: Mapped[str] = mapped_column(String(50),nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True)  
    hashed_password: Mapped[str] = mapped_column(String(255),nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(20),nullable=True)
    provider_id: Mapped[str] = mapped_column(String(100), nullable=True,unique=True)

    @classmethod
    async def check_user(cls, name: str, password: str, db: AsyncSession):
        result = await db.execute(select(cls).where(cls.name == name))
        user = result.scalar_one_or_none()
        if not user or not pass_settings.verify_password(plain_password=password,hashed_password=user.hashed_password):
            return None
        
        return {"id" : user.id,"name" : user.name}
        