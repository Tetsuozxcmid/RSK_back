from __future__ import annotations
from sqlalchemy import Boolean, Column, Integer, ForeignKey
from db.base import Base


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    is_leader = Column(Boolean, default=False)
