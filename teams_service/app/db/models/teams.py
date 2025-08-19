from __future__ import annotations
from db.base import Base
from db.models.teams_enums.enums import DirectionEnum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    direction = Column(Enum(DirectionEnum), nullable=False)
    city = Column(String)
    region = Column(String)
    organization_id = Column(Integer)
    organization_name = Column(String)
    leader_id = Column(Integer)
    members = relationship("TeamMember", backref="team", cascade="all, delete-orphan")