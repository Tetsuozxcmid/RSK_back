from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from shemas.team_shemas.team_register import TeamRegister
from cruds.teams_crud.crud import TeamCRUD
from shemas.team_shemas.team_update import TeamUpdate
from db.session import get_db
from services.grabber import get_current_user


router = APIRouter(prefix="/teams")


team_management_router = APIRouter(tags=["Team Management"])
team_membership_router = APIRouter(tags=["Team Membership"])
team_discovery_router = APIRouter(tags=["Team Discovery"])


@team_management_router.post("/register")
async def register_team(team_data: TeamRegister, request: Request, db: AsyncSession = Depends(get_db)):
    leader_id = await get_current_user(request)
    team = await TeamCRUD.create_team(db, team_data, leader_id=leader_id)
    return {
        "message": "Team registered successfully",
        "team_id": team.id,
        "leader_id": leader_id
    }

@team_management_router.delete('/delete_team/{team_id}')
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

@team_management_router.patch('/update_team_data/{team_id}')
async def update_team_data(team_id: int, update_data: TeamUpdate, db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.update_team(db=db, team_id=team_id, update_data=update_data.model_dump())
        return team
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@team_membership_router.post('/join_team/{team_id}')
async def join_team(
    team_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_id = await get_current_user(request)
    try:
        result = await TeamCRUD.join_team(db, team_id, user_id)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

@team_membership_router.get('/team_members/{team_id}')
async def get_team_members(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        members = await TeamCRUD.get_team_members_with_profiles(db, team_id)
        return members
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )

@team_membership_router.get('/my_teams/')
async def get_my_teams(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_id = await get_current_user(request)
    try:
        teams = await TeamCRUD.get_user_teams(db, user_id)
        return teams
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@team_discovery_router.get('/all_teams/')
async def get_all_teams(db: AsyncSession = Depends(get_db)):
    teams = await TeamCRUD.get_all_teams(db)
    return teams

@team_discovery_router.get('/get_team_by_id/{team_id}')
async def get_team_by_id(team_id: int, db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.get_team_by_id(team_id=team_id, db=db)
        return team
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"team with {team_id} not found")

@team_discovery_router.get('/get_team_by_organization/{org_id}')
async def get_team_by_org(org_id: int, db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.get_teams_by_organization(db=db, org_id=org_id)
        return team
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"not found")


router.include_router(team_management_router)
router.include_router(team_membership_router)
router.include_router(team_discovery_router)

