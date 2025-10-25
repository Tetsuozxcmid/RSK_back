from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_profile_client import UserProfileClient
from services.db_checker import OrgsClient
from db.models.teams import Team
from db.models.team_members import TeamMember
from fastapi import HTTPException
from services.bot_client import BotClient
import logging

class TeamCRUD:
    @staticmethod
    async def create_team(db: AsyncSession, team_data, leader_id: int):
        logging.info(f"User {leader_id} is trying to create team '{team_data.name}' in org '{team_data.organization_name}'")
        try:
            existing_member = await db.execute(
                select(TeamMember).where(TeamMember.user_id == leader_id)
            )
            if existing_member.scalar_one_or_none():
                logging.info(f"User {leader_id} already belongs to a team")
                raise HTTPException(
                    status_code=400,
                    detail="You already have a team. Leave your current team to create a new one"
                )

            existing_team = await db.execute(
                select(Team).where(Team.name == team_data.name)
            )
            
            if existing_team.scalar_one_or_none():
                logging.info(f"Team '{team_data.name}' already exists")
                raise HTTPException(
                    status_code=400,
                    detail="Team already exists"
                )

            org_exists = await OrgsClient.check_organization_exists(team_data.organization_name)
            org_id = await OrgsClient.get_organization_info(team_data.organization_name)
            if not org_exists:
                logging.info(f"Organization '{team_data.organization_name}' does not exist. Sending request to admin bot.")
                await BotClient.send_team_request_to_bot(
                    leader_id=leader_id,
                    team_name=team_data.name,
                    org_name=team_data.organization_name
                )
                raise HTTPException(
                    status_code=400,
                    detail="Organization doesn't exist. Admin notification sent, check later"
                )

            new_team = Team(
                name=team_data.name,
                direction=team_data.direction,
                region=team_data.region,
                leader_id=leader_id,
                organization_name=team_data.organization_name,
                organization_id=org_id["id"],
                points=team_data.points,
                description=team_data.description,
                tasks_completed=team_data.tasks_completed
            )
            
            db.add(new_team)
            await db.commit()
            await db.refresh(new_team)
            logging.info(f"Team '{new_team.name}' successfully created with ID {new_team.id}")

            team_member = TeamMember(
                team_id=new_team.id,
                user_id=leader_id,
                is_leader=True
            )
            db.add(team_member)
            await db.commit()
            logging.info(f"User {leader_id} added as leader to team '{new_team.name}'")


            await UserProfileClient.update_user_team(
                user_id=leader_id,
                team_name=new_team.name,
                team_id=new_team.id
            )

            await UserProfileClient.update_user_org(
                user_id=leader_id,
                organization_name=new_team.organization_name,
                organization_id=new_team.organization_id
            )

            return new_team

        except HTTPException as he:
            await db.rollback()
            logging.warning(f"HTTPException during team creation: {he.detail}")
            raise he
        except Exception as e:
            await db.rollback()
            logging.error(f"Failed to create team due to unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error while registering team: {str(e)}"
            )

        
    
    @staticmethod
    async def join_team(db: AsyncSession, team_id: int, user_id: int):
        existing_membership = await db.execute(
            select(TeamMember).where(TeamMember.user_id == user_id)
        )

        if existing_membership.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="You already belong to a team. Leave your current team first."
            )
        
        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        if team.number_of_members is None:
            team.number_of_members = 0

        if team.number_of_members >= 4:
            raise HTTPException(
                status_code=400,
                detail="Team is full. Maximum 4 members allowed."
            )
        
        team_member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            is_leader=False
        )

        db.add(team_member)
        team.number_of_members += 1
        
        try:
            await db.commit()
            await UserProfileClient.update_user_team(
                user_id=user_id,
                team_name=team.name,
                team_id=team_id
            )
            await UserProfileClient.update_user_org(
                user_id=user_id,
                organization_name=team.organization_name,
                organization_id=team.organization_id
            )
            
            return {"message": "Successfully joined the team"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error joining team: {str(e)}"
            )
        
    @staticmethod
    async def leave_team(db: AsyncSession, team_id: int, user_id: int):
        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()
        
        if team and team.leader_id == user_id:
            raise HTTPException(
                status_code=400,
                detail="Team leader cannot leave the team. Transfer leadership first or delete the team."
            )
        
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        team_member = result.scalar_one_or_none()
        
        if not team_member:
            raise HTTPException(status_code=400, detail="You are not a member of this team")
        
        try:
            if team and team.number_of_members is not None and team.number_of_members > 0:
                team.number_of_members -= 1

            await db.delete(team_member)
            await db.commit()
            
            await UserProfileClient.update_user_team(
                user_id=user_id,
                team_name="",  
                team_id=0      
            )

            await UserProfileClient.update_user_org(
                user_id=user_id,
                organization_name="",
                organization_id=0
            )
            
            return {"message": "Successfully left the team"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error leaving team: {str(e)}"
            )
        
    @staticmethod
    async def get_team_members(db: AsyncSession, team_id: int):
        result = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id)
        )
        members = result.scalars().all()
        
        return members
    
    @staticmethod
    async def get_user_teams(db: AsyncSession, user_id: int):
        result = await db.execute(
            select(TeamMember).where(TeamMember.user_id == user_id)
        )
        team_memberships = result.scalars().all()
        
        
        teams = []
        for membership in team_memberships:
            team_result = await db.execute(
                select(Team).where(Team.id == membership.team_id)
            )
            team = team_result.scalar_one_or_none()
            if team:
                teams.append({
                    "team": team,
                    "is_leader": membership.is_leader
                })
        
        return teams
    

    @staticmethod
    async def get_team_members_with_profiles(db: AsyncSession, team_id: int):
       
        result = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id)
        )
        members = result.scalars().all()
        
        if not members:
            return []
        
        
        user_ids = [member.user_id for member in members]
        
        
        users_profiles = await UserProfileClient.get_users_profiles(user_ids)
        
        
        members_with_profiles = []
        for member in members:
            user_profile = users_profiles.get(str(member.user_id), {})
            
            member_data = {
            "user_id": member.user_id,
            "team_id": member.team_id,
            "is_leader": member.is_leader,
            "name": user_profile.get("NameIRL", ""),
            "surname": user_profile.get("Surname", ""),
            "patronymic": user_profile.get("Patronymic", ""),
            "region": user_profile.get("Region", "")
            }

            members_with_profiles.append(member_data)
        
        return members_with_profiles

    @staticmethod
    async def delete_team(db: AsyncSession, team_id: int): 
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        
        if team is None:
            raise HTTPException(
                status_code=404,
                detail=f"Team with id {team_id} not found"
            )
        
        try:
            members_result = await db.execute(
                select(TeamMember).where(TeamMember.team_id == team_id)
            )
            members = members_result.scalars().all()

            await db.delete(team)
            await db.commit()
            
            for member in members:
                await UserProfileClient.update_user_team(
                    user_id=member.user_id,
                    team_name="",
                    team_id=0
                )
            
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
        

        
    
