from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.db_checker import OrgsClient
from db.models.teams import Team
from fastapi import HTTPException
from services.bot_client import BotClient

class TeamCRUD:
    @staticmethod
    async def create_team(db: AsyncSession, team_data, leader_id: int):
        exiting_team = await db.execute(
            select(Team).where(Team.name == team_data.name)
        )
        if exiting_team.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Team already exists"
            )
        
        org_exists = await OrgsClient.check_organization_exists(team_data.organization_name)
        if not org_exists:
            await BotClient.send_team_request_to_bot(
                leader_id=leader_id,
                team_name=team_data.name,
                org_name=team_data.organization_name
            )

            raise HTTPException(
            status_code=400,
            detail="Organization doesn't exist. Admin notification sent"
            )
            

        new_team = Team(
            name=team_data.name,
            direction=team_data.direction,
            city=team_data.city,
            region=team_data.region,
            organization_id=team_data.organization_id,
            leader_id=leader_id,
            organization_name=team_data.organization_name,
            
        )

        db.add(new_team)

        try:
            await db.commit()
            await db.refresh(new_team)
            return new_team

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error while registering team: {str(e)}"
            )
    
    
    @staticmethod
    async def delete_team(db: AsyncSession, team_id: int): 
        
        result = await db.execute(
            select(Team).where(Team.id == team_id)  
        )
        team = result.scalar_one_or_none()
        
        
        if team is None:  
            raise HTTPException(
                status_code=404,
                detail=f"Team with id {team_id} not found"
            )
        
        
        try:
            await db.delete(team)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error while deleting team: {str(e)}"
            )
        
    async def get_all_teams(db: AsyncSession):
        result = await db.execute(select(Team))
        teams = result.scalars().all()
        
        if not teams:
            return []
        
        return teams
    
    async def get_team_by_id(db: AsyncSession, team_id: int):
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return []
        
        return team
    
    @staticmethod
    async def update_team(db: AsyncSession, team_id: int, update_data: dict):
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        for key, value in update_data.items():
            setattr(team, key, value)
        
        try:
            await db.commit()
            await db.refresh(team)
            return team
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating team: {str(e)}")

    @staticmethod
    async def get_teams_by_organization(db: AsyncSession, org_id: int):
        result = await db.execute(select(Team).where(Team.organization_id == org_id))
        return result.scalars().all()
        

        
    