from __future__ import annotations
from sqlalchemy import Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
from db.models.user_enum import UserEnum

class User(Base):
    __tablename__ = 'user_profile'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, unique=True)
    username: Mapped[str] = mapped_column(String(100),nullable=True,default="")
    email: Mapped[str] = mapped_column(String(100),nullable=True,default="")

    NameIRL: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    Surname: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    Patronymic: Mapped[str] = mapped_column(String(100), nullable=True, default="")

    Description: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    Region: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    Type: Mapped[UserEnum] = mapped_column(SQLEnum(UserEnum), nullable=True, default=UserEnum.Student)

    Organization: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    Organization_id: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    team: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    team_id: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    

    

    