import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from db.models.orgs import Orgs
from fastapi import HTTPException
from schemas import OrgCreateSchema
import logging


class OrgsCRUD:
    @staticmethod
    async def get_org_by_name(db: AsyncSession, org_name: str):
        
        result = await db.execute(
            select(Orgs).where(func.lower(func.trim(Orgs.name)) == org_name.lower().strip())
        )
        return result.scalar_one_or_none()
    
    
    @staticmethod
    async def organization_exists(db: AsyncSession, org_name: str):
        result = await db.execute(
            select(Orgs).where(func.lower(func.trim(Orgs.name)) == org_name.lower().strip())
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_org(db: AsyncSession, org_name: str):
        org = await OrgsCRUD.get_org_by_name(db, org_name)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org
    
    @staticmethod
    async def get_org_by_id(db: AsyncSession, org_id: int):
        result = await db.execute(select(Orgs).where(Orgs.id == org_id))
        org = result.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org
        
    @staticmethod
    async def create_org_by_name(db: AsyncSession, org_name: str):
        new_org = Orgs(
                name=org_name,
            )
        db.add(new_org)
        await db.commit()
        await db.refresh(new_org)
        logging.info(f"organization '{new_org.name}' successfully created with ID {new_org.id}")
        return new_org

    @staticmethod
    async def get_orgs_paginated(db: AsyncSession, skip: int = 0, limit: int = 10):
        result = await db.execute(select(Orgs).offset(skip).limit(limit))
        return result.scalars().all()
    
    @staticmethod
    async def get_orgs_count(db: AsyncSession):
        result = await db.execute(select(func.count(Orgs.id)))
        return result.scalar_one()
    
    

