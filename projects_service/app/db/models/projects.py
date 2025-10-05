from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from db.base import Base

class TaskStatus(enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class CategoryEnum(enum.Enum):
    KNOWLEDGE = "KNOWLEDGE"
    INTERACTION = "INTERACTION"
    ENVIRONMENT = "ENVIRONMENT"
    PROTECTION = "PROTECTION"
    DATA = "DATA"
    AUTOMATION = "AUTOMATION"


CATEGORY_LABELS = {
    CategoryEnum.KNOWLEDGE: "Знания",
    CategoryEnum.INTERACTION: "Взаимодействие",
    CategoryEnum.ENVIRONMENT: "Среда",
    CategoryEnum.PROTECTION: "Защита",
    CategoryEnum.DATA: "Данные",
    CategoryEnum.AUTOMATION: "Автоматизация"
}


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    description = Column(Text)
    organization_name = Column(String)

    star_index = Column(Integer, nullable=False, default=0)
    star_category = Column(
    Enum(CategoryEnum, name="categoryenum"),  
    nullable=False
)

    level_number = Column(Integer, nullable=False, default=1)
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text)


    prize_points = Column(Integer, default=0)
    materials = Column(JSON, default=list)  


    status = Column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    team_id = Column(Integer, nullable=True)   
    leader_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="tasks")
    submissions = relationship("TaskSubmission", back_populates="task", cascade="all, delete-orphan")

class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    team_id = Column(Integer, nullable=False)

    text_description = Column(Text, nullable=True)
    result_url = Column(String, nullable=True)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(TaskStatus), default=TaskStatus.SUBMITTED)  

    moderator_id = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="submissions")