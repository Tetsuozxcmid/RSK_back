
import json
import aio_pika
from fastapi import APIRouter,HTTPException,Response,status,Depends, BackgroundTasks
from sqlalchemy import select

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
from services.emailsender import send_confirmation_email

from fastapi import APIRouter,Depends
from fastapi.responses import HTMLResponse
import os
from schemas.user_schemas.user_register import UserRegister,EmailSchema
from pathlib import Path
from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from services.rabbitmq import get_rabbitmq_connection
from sqlalchemy.ext.asyncio import AsyncSession
from aio_pika.abc import AbstractRobustConnection


router = APIRouter(prefix='/users_interaction')


auth_router = APIRouter(tags=['Authentication'])
email_router = APIRouter(tags=['Email Management'])
user_management_router = APIRouter(tags=['User Management'])


@auth_router.post('/register/')
async def register_user(
    user_data: UserRegister, 
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection), 
    background_tasks: BackgroundTasks = None
):
    try:
        user, confirmation_token = await UserCRUD.create_user(db, user_data)

        if background_tasks:
            background_tasks.add_task(
                send_confirmation_email,
                user.email,
                confirmation_token
            )
        else:
            asyncio.create_task(send_confirmation_email(user.email, confirmation_token))

        try:
            channel = await rabbitmq.channel()
            exchange = await channel.declare_exchange("user_events", type="direct", durable=True)

            user_data_message = {
                "user_id": user.id,
                "email": user.email,  
                "username": user.name,
                "verified": False,
                "event_type": "user_registered",
                "role" : user.role
            }

            message = aio_pika.Message(
                body=json.dumps(user_data_message).encode(),
                headers={"event_type": "user_events"},
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await exchange.publish(message, routing_key="user.created")

        except Exception as e:     
            print(f"Failed to send RabbitMQ message: {e}")
            
        return {
            "message": "User registered successfully. Please check your email for verification.",
            "user_id": user.id,
            "email": user.email,
            "username": user.name,
            "role":user.role
        }
        
    except HTTPException as e:
        raise e  
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@auth_router.post('/login/')
async def auth_user(response: Response, user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    password_str = user_data.password.get_secret_value()
    user = await User.check_user(name=user_data.name, password=password_str, db=db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect name or password")
    
    access_token = await create_access_token({"sub": str(user['id'])})
    response.set_cookie(key='users_access_token', value=access_token, httponly=True)

    return "Access successed"


@email_router.get('/confirm-email')
async def confirm_email(
    token: str, 
    db: AsyncSession = Depends(get_db),
    rabbitmq: AbstractRobustConnection = Depends(get_rabbitmq_connection)
):
    user = await UserCRUD.confirm_user_email(db, token)
    
    try:
        channel = await rabbitmq.channel()
        exchange = await channel.declare_exchange("user_events", type="direct", durable=True)
        role_value=user.role.value if hasattr(user.role,"value") else str(user.role)

        user_data_message = {
            "user_id": user.id,
            "email": user.email,  
            "username": user.name,
            "is_verified": True,
            "event_type": "user_verified",
            "role":role_value
        }
        message = aio_pika.Message(
            body=json.dumps(user_data_message).encode(),
            headers={"event_type": "user_verified"},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await exchange.publish(message, routing_key="user.verified")
    except Exception as e:     
        print(f"Failed to send RabbitMQ message: {e}")
    current_dir = Path(__file__).parent
    html_file_path = current_dir / "mailsend.html"
    if html_file_path.exists():
        html_content=html_file_path.read_text(encoding="utf-8")
        html_content= html_content.replace("{User_NAME}",user.name)
        return HTMLResponse(content=html_content,status_code=200)
    else:
        return HTMLResponse(content="<h1>confirmed</h1>",status_code=200)

@email_router.post('/resend-confirmation/')
async def resend_confirmation(
    email: str,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    import uuid
    new_token = str(uuid.uuid4())
    user.confirmation_token = new_token
    await db.commit()
    
    if background_tasks:
        background_tasks.add_task(send_confirmation_email, user.email, new_token)
    else:
        await send_confirmation_email(user.email, new_token)
    
    return {"message": "Confirmation email sent successfully"}


@user_management_router.get('/get_users/', description='Для админа будет токен')
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

@user_management_router.delete('/delete_user/')
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await UserCRUD.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@user_management_router.patch('/change_password/')
async def change_password(user_id: int, passwords: ChangePasswordSchema, db: AsyncSession = Depends(get_db)):
    try:
        await UserCRUD.change_user_password(
            db=db, 
            user_id=user_id, 
            old_password=passwords.current_password.get_secret_value(), 
            new_password=passwords.new_password.get_secret_value()
        )
        return {"message": "Password changed success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error is in {str(e)}")

@user_management_router.get('/get_user_by_id/{user_id}')
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await UserCRUD.get_user_by_id(db=db, user_id=user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"user with id {user_id} not found")
    

router.include_router(auth_router)
router.include_router(email_router)
router.include_router(user_management_router)
    

    

