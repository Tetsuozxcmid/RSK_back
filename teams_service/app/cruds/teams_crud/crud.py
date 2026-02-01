from sqlalchemy.future import select
from sqlalchemy import func
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
    async def get_user_role(user_id: int) -> str:
        user_info = await UserProfileClient.get_user_profile(user_id)

        print(f"DEBUG get_user_role: User {user_id} info: {user_info}")

        if not user_info:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        role = user_info.get("Type") or user_info.get("type") or user_info.get("role")
        print(f"DEBUG get_user_role: Found role field: {role}")

        if role:
            role = role.lower()

        if not role:
            print(f"DEBUG get_user_role: Available fields: {list(user_info.keys())}")
            raise HTTPException(
                status_code=400, detail=f"User {user_id} doesn't have a role assigned"
            )

        return role

    @staticmethod
    async def analyze_team_composition(db: AsyncSession, team_id: int):
        members = await TeamCRUD.get_team_members(db, team_id)

        student_count = 0
        teacher_count = 0

        for member in members:
            role = await TeamCRUD.get_user_role(member.user_id)
            if role == "student":
                student_count += 1
            elif role == "teacher":
                teacher_count += 1

        return {
            "students": student_count,
            "teachers": teacher_count,
            "total": len(members),
        }

    @staticmethod
    async def can_user_join_team(db: AsyncSession, team_id: int, user_id: int):
        print(
            f" DEBUG can_user_join_team: Called with user_id={user_id}, team_id={team_id}"
        )

        existing_membership = await db.execute(
            select(TeamMember).where(TeamMember.user_id == user_id)
        )
        if existing_membership.scalar_one_or_none():
            return False, "You already belong to another team"

        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()
        if not team:
            return False, "Team not found"

        composition = await TeamCRUD.analyze_team_composition(db, team_id)
        if composition["total"] >= 4:
            return False, "Team is full (1 student + 3 teachers)"

        print(f"DEBUG can_user_join_team: Before get_user_role, user_id={user_id}")
        user_role = await TeamCRUD.get_user_role(user_id)
        print(f"DEBUG can_user_join_team: After get_user_role, user_role={user_role}")

        if user_role == "student":
            if composition["students"] >= 1:
                return False, "Team already has a student"
            return True, "Can join as student"

        elif user_role == "teacher":
            if composition["teachers"] >= 3:
                return False, "Team already has 3 teachers"
            if composition["students"] == 0 and composition["total"] + 1 == 4:
                return (
                    False,
                    "Cannot add teacher - team must have exactly 1 student. No room left for student.",
                )
            return True, "Can join as teacher"

        else:
            return False, f"Role '{user_role}' cannot join teams"

    @staticmethod
    async def create_team(db: AsyncSession, team_data, leader_id: int):
        logging.info(f"User {leader_id} is trying to create team '{team_data.name}'")
        try:
            existing_member = await db.execute(
                select(TeamMember).where(TeamMember.user_id == leader_id)
            )
            if existing_member.scalar_one_or_none():
                logging.info(f"User {leader_id} already belongs to a team")
                raise HTTPException(
                    status_code=400,
                    detail="You already have a team. Leave your current team to create a new one",
                )

            existing_team = await db.execute(
                select(Team).where(Team.name == team_data.name)
            )

            if existing_team.scalar_one_or_none():
                logging.info(f"Team '{team_data.name}' already exists")
                raise HTTPException(status_code=400, detail="Team already exists")

            org_exists = await OrgsClient.check_organization_exists(
                team_data.organization_name
            )
            org_info = await OrgsClient.get_organization_info(
                team_data.organization_name
            )
            if not org_exists:
                logging.info(
                    f"Organization '{team_data.organization_name}' does not exist. Sending request to admin bot."
                )
                await BotClient.send_team_request_to_bot(
                    leader_id=leader_id,
                    team_name=team_data.name,
                    org_name=team_data.organization_name,
                )
                raise HTTPException(
                    status_code=400,
                    detail="Organization doesn't exist. Admin notification sent, check later",
                )

            new_team = Team(
                name=team_data.name,
                direction=team_data.direction,
                region=team_data.region,
                leader_id=leader_id,
                organization_name=team_data.organization_name,
                organization_id=org_info["id"],
                points=team_data.points,
                description=team_data.description,
                tasks_completed=team_data.tasks_completed,
                number_of_members=1,
            )

            db.add(new_team)
            await db.commit()
            await db.refresh(new_team)
            logging.info(
                f"Team '{new_team.name}' successfully created with ID {new_team.id}"
            )

            team_member_leader = TeamMember(
                team_id=new_team.id, user_id=leader_id, is_leader=True
            )
            db.add(team_member_leader)
            await db.commit()

            await UserProfileClient.update_user_team(
                user_id=leader_id, team_name=new_team.name, team_id=new_team.id
            )

            await UserProfileClient.update_user_org(
                user_id=leader_id,
                organization_name=new_team.organization_name,
                organization_id=new_team.organization_id,
            )

            return new_team

        except HTTPException as he:
            await db.rollback()
            logging.warning(f"HTTPException during team creation: {he.detail}")
            raise he
        except Exception as e:
            await db.rollback()
            logging.error(
                f"Failed to create team due to unexpected error: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Error while registering team: {str(e)}"
            )

    @staticmethod
    async def join_team(db: AsyncSession, team_id: int, user_id: int):
        print(f" DEBUG join_team: Called with user_id={user_id}, team_id={team_id}")

        existing_membership = await db.execute(
            select(TeamMember).where(TeamMember.user_id == user_id)
        )

        if existing_membership.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="You already belong to a team. Leave your current team first.",
            )

        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        print(f"DEBUG join_team: Before can_user_join_team, user_id={user_id}")
        can_join, message = await TeamCRUD.can_user_join_team(db, team_id, user_id)
        print(
            f"DEBUG join_team: After can_user_join_team, can_join={can_join}, message={message}"
        )

        if not can_join:
            raise HTTPException(status_code=400, detail=message)

        current_composition = await TeamCRUD.analyze_team_composition(db, team_id)

        team_member = TeamMember(team_id=team_id, user_id=user_id, is_leader=False)

        db.add(team_member)
        team.number_of_members = current_composition["total"] + 1

        try:
            await db.commit()
            await UserProfileClient.update_user_team(
                user_id=user_id, team_name=team.name, team_id=team_id
            )
            await UserProfileClient.update_user_org(
                user_id=user_id,
                organization_name=team.organization_name,
                organization_id=team.organization_id,
            )

            updated_composition = await TeamCRUD.analyze_team_composition(db, team_id)

            return {
                "message": "Successfully joined the team",
                "team_composition": updated_composition,
            }
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error joining team: {str(e)}")

    @staticmethod
    async def leave_team(db: AsyncSession, team_id: int, user_id: int):
        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()

        if team and team.leader_id == user_id:
            raise HTTPException(
                status_code=400,
                detail="Team leader cannot leave the team. Transfer leadership first or delete the team.",
            )

        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id, TeamMember.user_id == user_id
            )
        )
        team_member = result.scalar_one_or_none()

        if not team_member:
            raise HTTPException(
                status_code=400, detail="You are not a member of this team"
            )

        try:
            if (
                team
                and team.number_of_members is not None
                and team.number_of_members > 0
            ):
                team.number_of_members -= 1

            await db.delete(team_member)
            await db.commit()

            await UserProfileClient.update_user_team(
                user_id=user_id, team_name="", team_id=0
            )

            await UserProfileClient.update_user_org(
                user_id=user_id, organization_name="", organization_id=0
            )

            return {"message": "Successfully left the team"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error leaving team: {str(e)}")

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
                teams.append({"team": team, "is_leader": membership.is_leader})

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
        print(f"DEBUG: Getting profiles for user_ids: {user_ids}")

        users_profiles = await UserProfileClient.get_users_profiles(user_ids)
        print(f"DEBUG: Received profiles: {users_profiles}")

        members_with_profiles = []
        for member in members:
            user_profile = users_profiles.get(str(member.user_id), {})
            print(f"DEBUG: Profile for user {member.user_id}: {user_profile}")

            try:
                role = await TeamCRUD.get_user_role(member.user_id)
            except:
                role = "unknown"

            member_data = {
                "user_id": member.user_id,
                "team_id": member.team_id,
                "is_leader": member.is_leader,
                "username": user_profile.get("username", f"user{member.user_id}"),
                "name": user_profile.get("NameIRL", ""),
                "surname": user_profile.get("Surname", ""),
                "patronymic": user_profile.get("Patronymic", ""),
                "region": user_profile.get("Region", ""),
                "role": role,
                "email": user_profile.get("email", ""),
            }

            members_with_profiles.append(member_data)

        return members_with_profiles

    @staticmethod
    async def delete_team(db: AsyncSession, team_id: int):
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if team is None:
            raise HTTPException(
                status_code=404, detail=f"Team with id {team_id} not found"
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
                    user_id=member.user_id, team_name="", team_id=0
                )

            return True
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Database error while deleting team: {str(e)}"
            )

    @staticmethod
    async def get_all_teams(db: AsyncSession):
        result = await db.execute(select(Team))
        teams = result.scalars().all()

        if not teams:
            return []

        return teams

    @staticmethod
    async def get_team_by_id(db: AsyncSession, team_id: int):
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return None

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
            raise HTTPException(
                status_code=500, detail=f"Error updating team: {str(e)}"
            )

    @staticmethod
    async def get_teams_by_organization(db: AsyncSession, org_id: int):
        result = await db.execute(select(Team).where(Team.organization_id == org_id))
        return result.scalars().all()

    @staticmethod
    async def analyze_team_composition(db: AsyncSession, team_id: int):
        members = await TeamCRUD.get_team_members(db, team_id)

        print(
            f"DEBUG analyze_team_composition: Team {team_id} members: {[m.user_id for m in members]}"
        )

        student_count = 0
        teacher_count = 0

        for member in members:
            print(
                f"DEBUG analyze_team_composition: Getting role for member {member.user_id}"
            )
            role = await TeamCRUD.get_user_role(member.user_id)
            if role == "student":
                student_count += 1
            elif role == "teacher":
                teacher_count += 1

        return {
            "students": student_count,
            "teachers": teacher_count,
            "total": len(members),
        }

    @staticmethod
    async def get_team_count_by_id(
        db: AsyncSession, org_ids: list[int]
    ) -> dict[int, int]:
        if not org_ids:
            return {}

        query = (
            select(Team.organization_id, func.count(Team.id))
            .where(Team.organization_id.in_(org_ids))
            .group_by(Team.organization_id)
        )

        res = await db.execute(query)
        rows = res.all()

        counts = {org_id: 0 for org_id in org_ids}

        for org_id, cnt in rows:
            if org_id in counts:
                counts[org_id] = cnt

        return counts
