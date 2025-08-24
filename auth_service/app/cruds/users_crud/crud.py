import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from routes.users_router.auth_logic import pass_settings
from schemas.user_schemas.user_get import UserOut
from fastapi import HTTPException

class UserCRUD:
    @staticmethod
    async def create_user(db: AsyncSession, user_data):
        
        existing_user = await db.execute(
            select(User).where(
                (User.name == user_data.name) 
            )
        )
        
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail='User already registered'
            )

        
        password_str = user_data.password.get_secret_value()
        hashed_password = pass_settings.get_password_hash(password_str)

        
        confirmation_token = str(uuid.uuid4())
        
        
        new_user = User(
            name=user_data.name,
            hashed_password=hashed_password,
            email=user_data.email.lower(),  
            verified=False,  
            confirmation_token=confirmation_token  
        )
        
        db.add(new_user)
        
        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user, confirmation_token  
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error while registering user: {str(e)}"
            )
    
    # Добавляем метод для подтверждения email
    @staticmethod
    async def confirm_user_email(db: AsyncSession, token: str):
        result = await db.execute(
            select(User).where(User.confirmation_token == token)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Invalid confirmation token"
            )
        
        if user.verified:
            raise HTTPException(
                status_code=400,
                detail="Email already confirmed"
            )
        
        # Подтверждаем email
        user.verified = True
        user.confirmation_token = None  # удаляем токен после подтверждения
        
        try:
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error confirming email: {str(e)}"
            )
        
    async def get_all_users(db: AsyncSession):
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            if not users:  
                return []
                
            return [UserOut.from_orm(User) for User in users]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while fetching users: {str(e)}"
            )

    async def delete_user(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        try:
            await db.delete(user)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error while deleting user: {str(e)}"
            )
        
    async def change_user_password(db: AsyncSession, user_id: int,old_password: str, new_password: str):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
            status_code=404,
            detail="User not found"
        )   

        if not pass_settings.verify_password(old_password,user.hashed_password):
            raise HTTPException(
            status_code=400,
            detail="Incorrect current password"
        )

        new_hashed_password = pass_settings.get_password_hash(new_password)
        user.hashed_password = new_hashed_password

        try:
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500,detail=f"{str(e)}")
        
    async def get_user_by_id(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
            status_code=404,
            detail="User not found"
        )
        
        return {"name": user.name}

