from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, Enum as sqlEnum
from db.base import Base

from db.models.enums.submission_enum import SubmissionStatus

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        sqlEnum(SubmissionStatus, name="submission_status_enum"),
        default=SubmissionStatus.PENDING,
        nullable=False
    )