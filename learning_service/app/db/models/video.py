from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Enum as sqlEnum
from enum import Enum
from ..base import Base


class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    level: Mapped[UserLevel] = mapped_column(
        sqlEnum(UserLevel, name="user_level_enum"),
        nullable=False
    )