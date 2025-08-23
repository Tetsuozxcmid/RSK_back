
import json
import aio_pika
from fastapi import APIRouter,HTTPException,Response,status,Depends
from schemas.user_schemas.user_register import UserRegister
from schemas.user_schemas.user_password import ChangePasswordSchema
from schemas.user_schemas.user_auth import UserAuth
from schemas.user_schemas.user_get import UserGet
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from db.models.user import User
from services.jwt import create_access_token

from fastapi import APIRouter,Depends

from schemas.user_schemas.user_register import UserRegister

from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from services.rabbitmq import get_rabbitmq_connection
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika.abc import AbstractRobustConnection


router = APIRouter(prefix='/users_interaction',tags=['AuthSystem'])

@router.post('/register/')
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db),rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection)):
    user = await UserCRUD.create_user(db, user_data)

    try:
        channel = await rabbitmq.channel()
        exchange = await channel.declare_exchange("user_events",type="direct",durable=True)

        user_data_message = {
            "user_id": user.id,
            "email": user.email,  
            "username": user.name  
        }
        message = aio_pika.Message(
            body=json.dumps(user_data_message).encode(),
            headers={"event_type": "user_created"},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await exchange.publish(
            message,
            routing_key="user.created"
        )
    except Exception as e:     
        print(f"Failed to send RabbitMQ message: {e}")

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "email" : user.email,
        "username" : user.name
    }
    
@router.post('/login/')
async def auth_user(response:Response,user_data: UserAuth,db: AsyncSession = Depends(get_db)):
    password_str = user_data.password.get_secret_value()
    user = await User.check_user(name=user_data.name,password=password_str,db=db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect name or password")
    
    access_token = await create_access_token({"sub" : str(user['id'])})
    response.set_cookie(key='users_access_token',value=access_token,httponly=True)

    if response:
        return "Access successed"
    
@router.get('/get_users/',description='Для админа будет ток ')
async def get_all_users(db: AsyncSession = Depends(get_db)):
    
    try:
        users = await UserCRUD.get_all_users(db)
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch users: {str(e)}"
        )
    
@router.delete('/delete_user/')
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await UserCRUD.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.patch('/change_password/')
async def change_password(user_id: int, passwords: ChangePasswordSchema ,db: AsyncSession = Depends(get_db)):
    try:
        await UserCRUD.change_user_password(db=db,user_id=user_id,old_password=passwords.current_password.get_secret_value(),new_password=passwords.new_password.get_secret_value())
        return {
            "message" : "Password changed succes"
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"error is in {str(e)}")
    
@router.get('/get_user_by_id/{user_id}')
async def get_user_by_id(user_id: int,db: AsyncSession = Depends(get_db)):
    try:
        user = await UserCRUD.get_user_by_id(db=db,user_id=user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=404,detail=f"user with id {user_id} not found")
    

    

    

