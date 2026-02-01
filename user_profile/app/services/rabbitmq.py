import aio_pika
import json
from sqlalchemy import select
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker

ROLE_MAPPING = {
    "student": UserEnum.Student,
    "teacher": UserEnum.Teacher,
    "moder": UserEnum.Moder,
}


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
