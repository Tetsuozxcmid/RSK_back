from __future__ import annotations
from sqlalchemy import Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
from db.models.user_enum import UserEnum

class User(Base):
    __tablename__ = 'user_profile'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True,unique=True)
    NameIRL: Mapped[str] = mapped_column(String(100),nullable=True)  
    Surname: Mapped[str] = mapped_column(String(100),nullable=True)
    Patronymic: Mapped[str] = mapped_column(String(100),nullable=True)
    Description: Mapped[str] = mapped_column(String(500),nullable=True)
    Region: Mapped[str] = mapped_column(String(100),nullable=True)
    Type: Mapped[UserEnum] = mapped_column(SQLEnum(UserEnum),nullable=True)
    Organization: Mapped[str] = mapped_column(String(100),nullable=True)
    Organization_id: Mapped[int] = mapped_column(Integer,nullable=True)

    team: Mapped[str] = mapped_column(String(100),nullable=True)
    team_id: Mapped[int] = mapped_column(Integer,nullable=True)
    

    

    