
import asyncio
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker
from sqlalchemy import insert, select
import json

ROLE_MAPPING = {
        "student":UserEnum.Student,
        "teacher":UserEnum.Teacher,
}

async def consume_user_created_events(rabbitmq_url: str):
    while True:
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange("user_events", type="direct", durable=True)
                queue = await channel.declare_queue("user_profile_queue", durable=True)
                await queue.bind(exchange, routing_key="user.created")
                
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        try:
                            data = json.loads(message.body.decode())
                            user_id = data.get("user_id")
                            email = data.get("email","")
                            username = data.get("username","")
                            role_raw = data.get("role","")
                            if not isinstance(role_raw,str):
                                role_str = str(role_raw).lower()
                            else:
                                role_str = role_raw.lower()
                            if role_str not in ROLE_MAPPING:
                                continue
                            user_role = ROLE_MAPPING[role_str]
                            async with async_session_maker() as session:
                                
                                result = await session.execute(select(User).where(User.id == user_id))
                                user = result.scalar_one_or_none()
                                
                                if not user:
                                    
                                    new_profile = User(
                                        id=user_id,
                                        username=username,
                                        NameIRL="",
                                        email=email,
                                        Surname="",
                                        Type=user_role
                                    )

                                    session.add(new_profile)
                                    await session.commit()
                                    await message.ack()
                                else:
                                    
                                    await message.ack()
                                    
                        except Exception as e:
                            print(f"Error processing message: {e}")
                            await message.nack(requeue=False)
        except Exception as e:
            print(f"Connection error: {e}")
            await asyncio.sleep(5)
