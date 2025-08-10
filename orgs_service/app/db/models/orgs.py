from __future__ import annotations
from db.base import Base
from sqlalchemy import Column, Integer, String, Enum

class Orgs(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True,autoincrement=True)
    name = Column(String, nullable=False)
    