from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.orgs import Orgs
from fastapi import HTTPException
from schemas import OrgCreateSchema

class OrgsCRUD:
    @staticmethod
    async def get_org_by_name(db: AsyncSession,org_name: str):
        result = await db.execute(select(Orgs).where(Orgs.name == org_name))
        org = result.scalar_one_or_none()

        if not org:
            raise HTTPException(
            status_code=404,
            detail="Org not found"
        )
        
        return {"name": Orgs.name}
    
    async def add_org_by_name(db: AsyncSession, data: OrgCreateSchema):
        
        existing_org = await db.execute(
            select(Orgs).where(Orgs.name == data.name)
        )
        if existing_org.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Organization with this name already exists"
            )

        new_org = Orgs(
            name=data.name,
            
        )

        db.add(new_org)

        try:
            await db.commit()
            await db.refresh(new_org)
            return new_org
        except Exception as e:  
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating organization: {str(e)}"
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )

