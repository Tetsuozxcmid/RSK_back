from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.orgs_crud import OrgsCRUD
from schemas import OrgCreateSchema

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/count")
async def get_organizations_count(db: AsyncSession = Depends(get_db)):
    count = await OrgsCRUD.get_orgs_count(db)
    return {"count": count}

@router.get("/exists/{org_name}")
async def check_organization_exists(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org_by_name(db, org_name)
    return {"exists": org is not None}


@router.get("/{org_name}")
async def get_organization(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org(db, org_name)
    return {"id": org.id, "name": org.name}

@router.get("/org-id/{org_id}")
async def get_organization_by_id(org_id: int, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org_by_id(db, org_id)
    return {"id": org.id, "name": org.name}

@router.get("/")
async def get_organizations(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    orgs = await OrgsCRUD.get_orgs_paginated(db, skip=skip, limit=limit)
    return [{"id": org.id, "name": org.name} for org in orgs]

@router.post("/create")
async def create_org(request: OrgCreateSchema, db: AsyncSession = Depends(get_db)):
    org_name = request.name
    
    existing_org = await OrgsCRUD.get_org_by_name(db, org_name)
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")
    
    org = await OrgsCRUD.create_org_by_name(db, org_name)
    return {"id": org.id, "name": org.name}



