from fastapi import APIRouter, Depends, HTTPException, Request

from shemas.team_shemas.team_register import TeamRegister
from cruds.teams_crud.crud import TeamCRUD
from shemas.team_shemas.team_update import TeamUpdate
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.grabber import get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.post("/register")
async def register_team(team_data: TeamRegister,request: Request, db: AsyncSession = Depends(get_db)):
    leader_id = await get_current_user(request)
    team = await TeamCRUD.create_team(db, team_data, leader_id=leader_id)
    return {
        "message": "Team registered successfully",
        "team_id": team.id,
        "leader_id" : leader_id
    }

@router.get('/all_teams/')
async def get_all_teams(db: AsyncSession = Depends(get_db)):
    teams = await TeamCRUD.get_all_teams(db)
    return teams

@router.delete('/delete_team/{team_id}')
async def delete_team(
    team_id: int,  
    db: AsyncSession = Depends(get_db)
):
    try:
        await TeamCRUD.delete_team(db, team_id)
        return {"message": f"Team {team_id} deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )
    
@router.get('/get_team_by_id/{team_id}')
async def get_team_by_id(team_id: int, db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.get_team_by_id(team_id=team_id,db=db)
        return team
        
    except Exception as e:
        raise HTTPException(status_code=404,detail=f"team with {team_id} not found")
    
@router.get('/get_team_by_organization/{org_id}')
async def get_team_by_org(org_id: int,db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.get_teams_by_organization(db=db,org_id=org_id)
        return team
    except Exception as e:
        raise HTTPException(status_code=404,detail=f"not found")
    
@router.patch('/update_team_data/{team_id}')
async def update_team_data(team_id: int,update_data: TeamUpdate, db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.update_team(db=db,team_id=team_id,update_data=update_data.model_dump())
        return team
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"{str(e)}")

