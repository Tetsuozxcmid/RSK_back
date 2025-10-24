# routers/orgs_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.orgs_crud import OrgsCRUD

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/exists/{org_name}")
async def check_organization_exists(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org_by_name(db, org_name)
    return {"exists": org is not None}


@router.get("/{org_name}")
async def get_organization(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org(db, org_name)
    return {"id": org.id, "name": org.name}


@router.get("/")
async def get_organizations(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    orgs = await OrgsCRUD.get_orgs_paginated(db, skip=skip, limit=limit)
    return [{"id": org.id, "name": org.name} for org in orgs]

