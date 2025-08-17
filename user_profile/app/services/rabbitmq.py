
import asyncio
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker
from sqlalchemy import insert, select

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
                            user_id = int(message.body.decode())
                            async with async_session_maker() as session:
                                
                                result = await session.execute(select(User).where(User.id == user_id))
                                user = result.scalar_one_or_none()
                                
                                if not user:
                                    
                                    new_profile = User(
                                        id=user_id,
                                        NameIRL="",
                                        Surname="",
                                        Type=UserEnum.Student
                                        
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