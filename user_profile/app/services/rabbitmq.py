import aio_pika
import json
from datetime import datetime
from sqlalchemy import select
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker
from aio_pika.abc import AbstractRobustConnection
from fastapi import Request

ROLE_MAPPING = {
    "student": UserEnum.Student,
    "teacher": UserEnum.Teacher,
    "moder": UserEnum.Moder,
}


async def publish_role_update(
    rabbitmq_connection, 
    user_id: int, 
    new_role: str, 
    old_role: str = None
):
   
    try:
        channel = await rabbitmq_connection.channel()
        exchange = await channel.declare_exchange(
            "user_events", type="direct", durable=True
        )
        
        message_data = {
            "user_id": user_id,
            "new_role": new_role,
            "old_role": old_role,
            "event_type": "user.role_updated",
            "timestamp": str(datetime.utcnow())
        }
        
        message = aio_pika.Message(
            body=json.dumps(message_data).encode(),
            headers={"event_type": "user.role_updated"},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        
        await exchange.publish(message, routing_key="user.role_updated")
        print(f"[PUBLISHER] Role update published for user {user_id}: {old_role} -> {new_role}")
        
    except Exception as e:
        print(f"[PUBLISHER] Failed to publish role update: {e}")
        raise  


async def consume_user_created_events(rabbitmq_url: str):
   
    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        "user_events", type="direct", durable=True
    )

    queue = await channel.declare_queue("user_profile_queue", durable=True)

    await queue.bind(exchange, routing_key="user.created")

    print("[CONSUMER] Waiting for user.created events...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                data = json.loads(message.body.decode())

                user_id = data.get("user_id")
                email = data.get("email", "")
                username = data.get("username", "")
                name = data.get("name", "")
                role_raw = data.get("role", "")

                role_str = str(role_raw).lower()
                if role_str not in ROLE_MAPPING:
                    print(f"[CONSUMER] Unknown role: {role_raw}, user_id={user_id}")
                    await message.ack()
                    continue

                user_role = ROLE_MAPPING[role_str]

                async with async_session_maker() as session:
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()

                    if not user:
                        new_profile = User(
                            id=user_id,
                            username=username,
                            NameIRL=name or "",
                            email=email,
                            Surname="",
                            Type=user_role,
                        )
                        session.add(new_profile)
                        await session.commit()
                        print(f"[CONSUMER] Profile created for user_id={user_id}")
                    else:
                        print(
                            f"[CONSUMER] Profile already exists for user_id={user_id}"
                        )

                await message.ack()

            except Exception as e:
                print(f"[CONSUMER] Error processing message: {e}")
                await message.nack(requeue=False)


async def get_rabbitmq_connection(request: Request) -> AbstractRobustConnection:
    
    return request.app.state.rabbitmq_connection


async def consume_role_updated_events(rabbitmq_url: str):
    
    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        "user_events", type="direct", durable=True
    )

    queue = await channel.declare_queue("user_profile_role_queue", durable=True)

    await queue.bind(exchange, routing_key="user.role_updated")

    print("[CONSUMER] Waiting for user.role_updated events...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                data = json.loads(message.body.decode())

                user_id = data.get("user_id")
                new_role = data.get("new_role")
                old_role = data.get("old_role")

                print(f"[CONSUMER] Received role update for user {user_id}: {old_role} -> {new_role}")

                role_str = str(new_role).lower()
                if role_str not in ROLE_MAPPING:
                    print(f"[CONSUMER] Unknown role: {new_role}, user_id={user_id}")
                    await message.ack()
                    continue

                new_role_enum = ROLE_MAPPING[role_str]

                async with async_session_maker() as session:
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()

                    if user:
                        user.Type = new_role_enum
                        await session.commit()
                        print(f"[CONSUMER] Role updated for user_id={user_id} to {new_role}")
                    else:
                        print(f"[CONSUMER] User {user_id} not found")

                await message.ack()

            except Exception as e:
                print(f"[CONSUMER] Error processing message: {e}")
                await message.nack(requeue=False)