from services.user_profile_client import UserProfileClient
from fastapi import APIRouter, Depends, HTTPException, Request, Query
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
async def register_team(
    team_data: TeamRegister, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
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

@team_membership_router.delete('/leave_team/{team_id}')
async def leave_team(
    team_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_id = await get_current_user(request)
    try:
        result = await TeamCRUD.leave_team(db, team_id, user_id)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@team_membership_router.get('/can_join_team/{team_id}')
async def check_can_join_team(
    team_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_id = await get_current_user(request)
    can_join, message = await TeamCRUD.can_user_join_team(db, team_id, user_id)
    
    return {
        "can_join": can_join,
        "message": message
    }

@team_discovery_router.get('/all_teams/')
async def get_all_teams(db: AsyncSession = Depends(get_db)):
    teams = await TeamCRUD.get_all_teams(db)
    return teams

@team_discovery_router.get('/get_team_by_id/{team_id}')
async def get_team_by_id(team_id: int, db: AsyncSession = Depends(get_db)):
    try:
        team = await TeamCRUD.get_team_by_id(db, team_id)  
        if not team:
            raise HTTPException(status_code=404, detail=f"Team with id {team_id} not found")
            

        members = await TeamCRUD.get_team_members_with_profiles(db, team_id)
        

        composition = await TeamCRUD.analyze_team_composition(db, team_id)
        

        leader_info = None
        if team.leader_id:
            leader_profile = await UserProfileClient.get_user_profile(team.leader_id)
            if leader_profile:
                leader_info = {
                    "user_id": team.leader_id,
                    "username": leader_profile.get("username", ""),
                    "name": leader_profile.get("NameIRL", ""),
                    "surname": leader_profile.get("Surname", ""),
                    "role": await TeamCRUD.get_user_role(team.leader_id)
                }
        
        return {
            "team_info": {
                "id": team.id,
                "name": team.name,
                "direction": team.direction,
                "region": team.region,
                "leader_id": team.leader_id,
                "leader_info": leader_info,
                "organization_name": team.organization_name,
                "organization_id": team.organization_id,
                "points": team.points,
                "description": team.description,
                "tasks_completed": team.tasks_completed,
                "number_of_members": team.number_of_members,
                "created_at": team.created_at if hasattr(team, 'created_at') else None
            },
            "members": members,  
            "composition": composition,
            "available_slots": {
                "students": max(0, 1 - composition["students"]),
                "teachers": max(0, 3 - composition["teachers"]),
                "total": max(0, 4 - composition["total"])
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in get_team_by_id: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Team with id {team_id} not found")

@team_discovery_router.get('/get_team_by_organization/{org_id}')
async def get_team_by_org(org_id: int, db: AsyncSession = Depends(get_db)):
    try:
        teams = await TeamCRUD.get_teams_by_organization(db=db, org_id=org_id)
        return teams
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"No teams found for organization {org_id}")

@team_management_router.get("/teams-count")
async def get_members_count(
    org_ids: list[int] = Query(...),
    db: AsyncSession = Depends(get_db),
):
    counts = await TeamCRUD.get_team_count_by_id(
        db=db,
        org_ids=org_ids
    )
    return counts

router.include_router(team_management_router)
router.include_router(team_membership_router)
router.include_router(team_discovery_router)
