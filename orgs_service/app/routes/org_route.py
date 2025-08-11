from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from cruds.orgs_crud import OrgsCRUD
from schemas import OrgCreateSchema
from cruds.orgs_crud import OrgsCRUD
from fastapi import status

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/exists/{org_name}")
async def check_organization_exists(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org_by_name(db, org_name)
    return {"exists": org is not None}


@router.post("/create/", status_code=status.HTTP_201_CREATED)
async def add_org_new(data: OrgCreateSchema, db: AsyncSession = Depends(get_db)):
    return await OrgsCRUD.add_org_by_name(db, data)
