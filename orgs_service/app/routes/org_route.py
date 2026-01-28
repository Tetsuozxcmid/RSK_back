from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from db.parser import import_excel_to_sql
from cruds.orgs_crud import OrgsCRUD
from schemas import OrgCreateSchema


router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.post("/create")
async def create_org(request: OrgCreateSchema, db: AsyncSession = Depends(get_db)):
    inn = request.inn
    org = await OrgsCRUD.create_org_by_inn(db, inn)
    return "ok"



@router.get("/count")
async def get_organizations_count(db: AsyncSession = Depends(get_db)):
    count = await OrgsCRUD.get_orgs_count(db)
    return {"count": count}

@router.get("/all")
async def get_all_organizations(
    region: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),

    sort_by: Literal["name", "members", "index"] = Query(default="name"),
    order: Literal["asc", "desc"] = Query(default="asc"),

    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),

    db: AsyncSession = Depends(get_db),
):
    orgs = await OrgsCRUD.get_orgs(
        db=db,
        region=region,
        name=name,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return orgs

@router.get("/import_from_excel")
def import_from_excel():
    try:
        import_excel_to_sql(
            excel_path="/app/app/db/result_full.xlsx",
            sheet_name="Sheet1",
            table_name="organizations",
            if_exists="append",
            chunk_size=2000,
            drop_duplicates_by_kpp=True,
        )
        return {"status": "ok", "message": "Импорт выполнен"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/exists/{org_name}")
async def check_organization_exists(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org_by_name(db, org_name)
    return {"exists": org is not None}


@router.get("/{org_name}")
async def get_organization(org_name: str, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org(db, org_name)
    return {"id": org.id, "name": org.name}

@router.get("/org/{org_id}")
async def get_organization_by_id(org_id: int, db: AsyncSession = Depends(get_db)):
    org = await OrgsCRUD.get_org_by_id(db, org_id)
    return {
        "id": org.id,
        "full_name": org.full_name,
        "short_name": org.short_name,
        "inn": org.inn,
        "region": org.region,
        "type": org.type,
        "star": org.star,
        "knowledge_skills_z": org.knowledge_skills_z,
        "knowledge_skills_v": org.knowledge_skills_v,
        "digital_env_e": org.digital_env_e,
        "data_protection_z": org.data_protection_z,
        "data_analytics_d": org.data_analytics_d,
        "automation_a": org.automation_a,
        "members_count": org.members_count,
        "teams_count": org.teams_count
    }


