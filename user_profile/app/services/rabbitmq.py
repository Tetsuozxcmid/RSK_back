
import asyncio
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker
from sqlalchemy import insert

async def consume_user_created_events(rabbitmq_url: str):
    while True:
        try:

            connection = await aio_pika.connect_robust(rabbitmq_url)

            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange("user_events", type="direct", durable=True)
                queue = await channel.declare_queue("user_profile_queue", durable=True)
                await queue.bind(exchange, routing_key="user.created")
                
                print("RabbitMQ consumer ready")
                
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        try:
                            user_id = int(message.body.decode())
                            print(f"Processing user_id: {user_id}")
                            
                            async with async_session_maker() as session:
                                try:
                                    stmt = insert(User).values(
                                        id=user_id,
                                        NameIRL="",  
                                        Surname="",
                                        Patronymic="",
                                        Description="",
                                        Region="",
                                        Type=UserEnum.Student,  
                                        Organization="",
                                        Organization_id=0,
                                        team="",
                                        team_id=0
                                        )
                                    
                                    await session.execute(stmt)
                                    await session.commit()
                                    print(f"Saved user {user_id} to profile DB back")
                                    await message.ack()  
                                    
                                except Exception as e:
                                    print(f"DB Error: {e}")
                                    await session.rollback()
                                    await message.nack(requeue=False)  
                                    
                        except Exception as e:
                            print(f"Message processing failed: {e}")
                            await message.nack(requeue=False)
                            
        except Exception as e:
            print(f"RabbitMQ connection failed: {e}, retrying in 5s...")
            await asyncio.sleep(5)