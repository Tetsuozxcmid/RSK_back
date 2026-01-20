from __future__ import annotations
from db.base import Base
from db.models.org_enum import OrgType

from sqlalchemy import Column, Integer, String, Enum, Float, BigInteger


class Orgs(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    kpp = Column(BigInteger, nullable=False, unique=True)
    region = Column(String, nullable=False)
    type = Column(Enum(OrgType, name="org_type_enum"), nullable=False)
    
    star = Column(Float, nullable=False, default=0.0)

    knowledge_skills_z = Column(Float, nullable=False, default=0.0)
    knowledge_skills_v = Column(Float, nullable=False, default=0.0)
    digital_env_e = Column(Float, nullable=False, default=0.0)
    data_protection_z = Column(Float, nullable=False, default=0.0)
    data_analytics_d = Column(Float, nullable=False, default=0.0)
    automation_a = Column(Float, nullable=False, default=0.0)
