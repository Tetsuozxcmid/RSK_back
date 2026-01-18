from __future__ import annotations
from db.base import Base
from sqlalchemy import Column, Float, Integer, String, Enum
from db.models.org_enum import OrgType

class Orgs(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=True)
    short_name = Column(String, nullable=True)
    inn = Column(Integer, nullable=True, unique=True)
    region = Column(String, nullable=True)
    type = Column(Enum(OrgType, name="org_type_enum"), nullable=True)
    
    star = Column(Float, nullable=True, default=0.0)

    knowledge_skills_z = Column(Float, nullable=True, default=0.0)
    knowledge_skills_v = Column(Float, nullable=True, default=0.0)
    digital_env_e = Column(Float, nullable=True, default=0.0)
    data_protection_z = Column(Float, nullable=True, default=0.0)
    data_analytics_d = Column(Float, nullable=True, default=0.0)
    automation_a = Column(Float, nullable=True, default=0.0)
    