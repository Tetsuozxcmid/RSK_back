import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from db.models.user_enum import UserEnum, UserEnumForAdmin, UserEnumForUser
from db.models.user import User
from fastapi import HTTPException
from schemas.user import (
    OAuthProfileSyncRequest,
    OrganizationSimple,
    ProfileResponse,
    ProfileUpdate,
)
from services.orgs_client import OrgsClient


class ProfileCRUD:
    @staticmethod
    def _normalize_text(value: str | None) -> str:
        return str(value or "").strip()

    @staticmethod
    def _split_full_name(full_name: str | None) -> tuple[str, str, str]:
        parts = [part for part in ProfileCRUD._normalize_text(full_name).split() if part]
        if len(parts) < 2:
            return "", "", ""

        first_name = parts[0]
        last_name = parts[1]
        patronymic = " ".join(parts[2:]).strip() if len(parts) > 2 else ""
        return first_name, last_name, patronymic

    @staticmethod
    def _resolve_role(role_raw: str | UserEnum | None) -> UserEnum:
        if isinstance(role_raw, UserEnum):
            return role_raw

        role_mapping = {
            "student": UserEnum.Student,
            "teacher": UserEnum.Teacher,
            "moder": UserEnum.Moder,
            "admin": UserEnum.Admin,
        }
        return role_mapping.get(
            ProfileCRUD._normalize_text(str(role_raw or "")).lower(),
            UserEnum.Student,
        )

    @staticmethod
    def _should_replace_username(
        current_username: str | None,
        incoming_username: str | None,
        auth_provider: str | None,
    ) -> bool:
        current = ProfileCRUD._normalize_text(current_username)
        incoming = ProfileCRUD._normalize_text(incoming_username)
        provider = ProfileCRUD._normalize_text(auth_provider).lower()

        if not incoming:
            return False
        if not current:
            return True
        if current == incoming:
            return False
        return provider in {"vk", "yandex"}

    @classmethod
    async def sync_oauth_profile(
        cls, db: AsyncSession, sync_data: OAuthProfileSyncRequest
    ):
        first_name = cls._normalize_text(sync_data.first_name)
        last_name = cls._normalize_text(sync_data.last_name)
        patronymic = cls._normalize_text(sync_data.patronymic)
        full_name = cls._normalize_text(sync_data.full_name)
        email = cls._normalize_text(sync_data.email)
        username = cls._normalize_text(sync_data.username) or f"user{sync_data.user_id}"
        auth_provider = cls._normalize_text(sync_data.auth_provider).lower()

        parsed_first_name, parsed_last_name, parsed_patronymic = cls._split_full_name(
            full_name
        )
        if not first_name:
            first_name = parsed_first_name
        if not last_name:
            last_name = parsed_last_name
        if not patronymic:
            patronymic = parsed_patronymic

        incoming_short_name = " ".join(
            part for part in [first_name, last_name] if part
        ).strip()
        incoming_full_name = full_name or " ".join(
            part for part in [first_name, last_name, patronymic] if part
        ).strip()

        result = await db.execute(select(User).where(User.id == sync_data.user_id))
        profile = result.scalar_one_or_none()
        created = False

        if not profile:
            profile = User(
                id=sync_data.user_id,
                username=username,
                email=email,
                NameIRL=first_name,
                Surname=last_name,
                Patronymic=patronymic,
                Type=cls._resolve_role(sync_data.role),
            )
            db.add(profile)
            created = True
        else:
            current_name = cls._normalize_text(profile.NameIRL)
            current_surname = cls._normalize_text(profile.Surname)
            current_patronymic = cls._normalize_text(profile.Patronymic)

            if cls._should_replace_username(profile.username, username, auth_provider):
                profile.username = username

            if email and not cls._normalize_text(profile.email):
                profile.email = email

            if first_name and not current_name:
                profile.NameIRL = first_name
                current_name = first_name

            if last_name and not current_surname:
                if current_name in {incoming_full_name, incoming_short_name}:
                    profile.NameIRL = first_name or current_name
                profile.Surname = last_name
                current_surname = last_name

            if patronymic and not current_patronymic:
                profile.Patronymic = patronymic

            if profile.Type is None:
                profile.Type = cls._resolve_role(sync_data.role)

        try:
            await db.commit()
            await db.refresh(profile)
            return {
                "status": "success",
                "created": created,
                "user_id": profile.id,
                "profile_complete": bool(
                    cls._normalize_text(profile.NameIRL)
                    and cls._normalize_text(profile.Surname)
                ),
            }
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error syncing OAuth profile: {str(e)}"
            )

    @staticmethod
    async def create_profile(db: AsyncSession, profile_data):
        exiting_profile = await db.execute(
            select(User).where(User.NameIRL == profile_data.NameIRL)
        )
        if exiting_profile.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Profile already exists")

        new_profile = User(
            NameIRL=profile_data.NameIRL,
            Surname=profile_data.Surname,
            Patronymic=profile_data.Patronymic,
            Description=profile_data.Description,
            Region=profile_data.Region,
            Type=profile_data.Type,
            Organization=profile_data.Organization,
        )

        db.add(new_profile)

        try:
            await db.commit()
            await db.refresh(new_profile)
            return new_profile

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while registering team: {str(e)}"
            )

    @staticmethod
    async def get_my_profile(db: AsyncSession, user_id: int):
        existing_profile = await db.execute(select(User).where(User.id == user_id))
        profile = existing_profile.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        organization_info = None
        if profile.Organization_id and profile.Organization_id > 0:
            org_data = await OrgsClient.get_organization_by_id(profile.Organization_id)

            if org_data:
                organization_info = OrganizationSimple(
                    id=org_data.get("id"),
                    name=org_data.get("short_name") or org_data.get("full_name"),
                    full_name=org_data.get("full_name"),
                    short_name=org_data.get("short_name"),
                    inn=org_data.get("inn"),
                    region=org_data.get("region"),
                    type=org_data.get("type"),
                )

        profile_data = {
            "NameIRL": profile.NameIRL,
            "email": profile.email,
            "username": profile.username,
            "Surname": profile.Surname,
            "Patronymic": profile.Patronymic,
            "Description": profile.Description,
            "Region": profile.Region,
            "Type": profile.Type,
            "Organization_id": profile.Organization_id,
            "Organization": organization_info,
            "team": profile.team,
            "team_id": profile.team_id,
            "is_learned": profile.is_learned,
        }

        return ProfileResponse(**profile_data)

    @staticmethod
    async def update_my_profile(
        db: AsyncSession, update_data: ProfileUpdate, user_id: int
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        update_dict = update_data.dict(exclude_unset=True)

        for field in [
            "NameIRL",
            "Surname",
            "Patronymic",
            "Description",
            "Region",
            "Organization_id",
            "email",
            "Type",
        ]:
            if field in update_dict:
                setattr(existing_profile, field, update_dict[field])

        try:
            await db.commit()
            await db.refresh(existing_profile)
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"something got wrong {e}")

    @staticmethod
    async def update_my_role(db: AsyncSession, user_id: int, new_role: UserEnumForUser):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")

        old_role = user.Type
        user.Type = new_role

        try:
            await db.commit()
            await db.refresh(user)
            return user, old_role
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error updating role: {str(e)},must be student or teacher",
            )

    @staticmethod
    async def update_user_role(
        db: AsyncSession, user_id: int, new_role: UserEnumForAdmin
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

        old_role = user.Type
        user.Type = new_role

        try:
            await db.commit()
            await db.refresh(user)
            return user, old_role
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error updating role: {str(e)}, must be admin or moder",
            )

    @staticmethod
    async def get_all_users_profiles(db: AsyncSession):
        result = await db.execute(select(User))
        return result.scalars().all()

    @staticmethod
    async def update_profile(update_data: ProfileUpdate, db: AsyncSession):
        result = await db.execute(select(User).where(User.id == update_data.id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        for field, value in update_data.dict(exclude_unset=True).items():
            if field != "id":
                setattr(existing_profile, field, value)

        try:
            await db.commit()
            await db.refresh(existing_profile)
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while updating profile: {str(e)}"
            )

    @staticmethod
    async def update_profile_joined_team(
        db: AsyncSession, user_id: int, team_name: str, team_id: int
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        existing_profile.team = team_name
        existing_profile.team_id = team_id

        try:
            await db.commit()
            await db.refresh(existing_profile)
            logging.info(f"User {user_id} joined team '{team_name}' (ID: {team_id})")
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while updating profile: {str(e)}"
            )

    @staticmethod
    async def update_profile_joined_org(
        db: AsyncSession, user_id: int, organization_name: str, organization_id: int
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        existing_profile = result.scalar_one_or_none()

        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        existing_profile.Organization = organization_name
        existing_profile.Organization_id = organization_id

        try:
            await db.commit()
            await db.refresh(existing_profile)
            logging.info(
                f"User {user_id} team is in org '{organization_name}' (ID: {organization_id})"
            )
            return existing_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error while updating profile: {str(e)}"
            )

    @staticmethod
    async def get_users_by_org_id(db: AsyncSession, org_id: int):
        result = await db.execute(select(User).where(User.Organization_id == org_id))
        return result.scalars().all()

    @staticmethod
    async def get_member_count_by_id(db: AsyncSession, org_ids: list[int]):
        res = await db.execute(
            select(User.Organization_id, func.count(User.id))
            .where(User.Organization_id.in_(org_ids))
            .group_by(User.Organization_id)
        )
        rows = res.all()

        counts = {org_id: 0 for org_id in org_ids}
        for org_id, cnt in rows:
            counts[org_id] = cnt

        return counts
