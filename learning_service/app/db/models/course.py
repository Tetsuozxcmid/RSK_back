from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from db.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lesson_name: Mapped[str] = mapped_column(String(200), nullable=False)
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    download_url: Mapped[str] = mapped_column(String(500), nullable=False)
