import logging
import httpx
from typing import Optional, Literal
from dadata import DadataAsync
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy.inspection import inspect
from db.models.orgs import Orgs
from fastapi import HTTPException
from config import settings

SortBy = Literal["name", "members"]
SortOrder = Literal["asc", "desc"]

dadata = DadataAsync(token=settings.DADATA_TOKEN, secret=settings.DADATA_SECRET)

class OrgsCRUD:
    @staticmethod
    async def get_org_by_name(db: AsyncSession, org_name: str):
        
        result = await db.execute(
            select(Orgs).where(func.lower(func.trim(Orgs.full_name)) == org_name.lower().strip())
        )
        return result.scalar_one_or_none()
    
    
    @staticmethod
    async def organization_exists(db: AsyncSession, org_name: str):
        result = await db.execute(
            select(Orgs).where(func.lower(func.trim(Orgs.full_name)) == org_name.lower().strip())
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
    async def create_org_by_inn(db: AsyncSession, inn: int):
        result = await dadata.find_by_id("party", str(inn))

        if isinstance(result, dict):
            suggestions = result.get("suggestions", [])
        elif isinstance(result, list):
            suggestions = result
        else:
            suggestions = []

        if not suggestions:
            return None

        suggestion = next(
            (s for s in suggestions if s.get("data", {}).get("branch_type") == "MAIN"),
            suggestions[0],
        )

        name_block = suggestion.get("data", {}).get("name", {})

        full_name = (name_block.get("full_with_opf") or suggestion.get("value") or "").strip()

        short_raw = (
            name_block.get("short_with_opf")
            or name_block.get("short")
            or suggestion.get("value")
            or ""
        )
        short_name = short_raw.split(",")[0].strip()

        address_data = suggestion.get("data", {}).get("address", {}).get("data", {})
        region = address_data.get("region_with_type")

        print(full_name, short_name, region)


    @staticmethod
    async def get_orgs_count(db: AsyncSession):
        result = await db.execute(select(func.count(Orgs.id)))
        return result.scalar_one()


    @staticmethod
    def org_to_dict(org: Orgs) -> dict:
        data = {c.key: getattr(org, c.key) for c in inspect(org).mapper.column_attrs}

        # если type = Enum объект, то сделаем строкой
        if hasattr(org.type, "value"):
            data["type"] = org.type.value

        return data

    @staticmethod
    async def get_orgs(
        db: AsyncSession,
        region: Optional[str] = None,
        name: Optional[str] = None,
        sort_by: SortBy = "name",
        order: SortOrder = "asc",
        limit: int = 50,
        offset: int = 0,
    ):
        stmt = select(Orgs)

        if name:
            stmt = stmt.where(Orgs.full_name.ilike(f"%{name}%"))

        if region:
            stmt = stmt.where(Orgs.region == region)

        if sort_by == "name":
            stmt = stmt.order_by(
                Orgs.full_name.asc() if order == "asc" else Orgs.full_name.desc()
            )
            stmt = stmt.offset(offset).limit(limit)

            res = await db.execute(stmt)
            orgs = res.scalars().all()
            return [OrgsCRUD.org_to_dict(o) for o in orgs]

        if sort_by == "members":
            res = await db.execute(stmt)
            orgs = res.scalars().all()

            if not orgs:
                return []

            org_ids = [o.id for o in orgs]

            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{settings.USERS_SERVICE_URL}/profile_interaction/members-count",
                    params=[("org_ids", oid) for oid in org_ids],
                )

            if r.status_code != 200:
                raise HTTPException(status_code=502, detail="Users service unavailable")

            counts = {int(k): v for k, v in r.json().items()}

            orgs.sort(
                key=lambda o: counts.get(o.id, 0),
                reverse=(order == "desc"),
            )

            sliced = orgs[offset: offset + limit]

            result = []
            for o in sliced:
                data = OrgsCRUD.org_to_dict(o)
                data["members_count"] = counts.get(o.id, 0)
                result.append(data)

            return result

        raise HTTPException(status_code=400, detail="Invalid sort_by value")
