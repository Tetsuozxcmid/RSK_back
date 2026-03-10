import asyncio

import aio_pika
import json
from datetime import datetime
from sqlalchemy import select
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker
from aio_pika.abc import AbstractRobustConnection
from fastapi import Request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROLE_MAPPING = {
    "student": UserEnum.Student,
    "teacher": UserEnum.Teacher,
    "moder": UserEnum.Moder,
    "admin": UserEnum.Admin,
}


async def publish_role_update(
    rabbitmq_connection, user_id: int, new_role: str, old_role: str = None
):
    try:
        logger.info(f"[PUBLISHER] Attempting to publish role update for user {user_id}: {old_role} -> {new_role}")
        
        channel = await rabbitmq_connection.channel()
        exchange = await channel.declare_exchange(
            "user_events", type="direct", durable=True
        )

        message_data = {
            "user_id": user_id,
            "new_role": new_role,
            "old_role": old_role,
            "event_type": "user.role_updated",
            "timestamp": str(datetime.utcnow()),
        }

        message = aio_pika.Message(
            body=json.dumps(message_data).encode(),
            headers={"event_type": "user.role_updated"},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await exchange.publish(message, routing_key="user.role_updated")
        logger.info(f"[PUBLISHER] ✅ Role update published for user {user_id}: {old_role} -> {new_role}")

    except Exception as e:
        logger.error(f"[PUBLISHER] ❌ Failed to publish role update: {e}", exc_info=True)
        raise


async def consume_user_created_events(rabbitmq_url: str):
    """
    Consumer для создания профилей при регистрации новых пользователей
    """
    print(f"\n🔵 [CONSUMER] {'='*50}")
    print(f"🔵 [CONSUMER] Starting user.created consumer")
    print(f"🔵 [CONSUMER] RabbitMQ URL: {rabbitmq_url}")
    print(f"🔵 [CONSUMER] {'='*50}\n")
    
    try:
        # Подключение к RabbitMQ
        print(f"🔵 [CONSUMER] Connecting to RabbitMQ...")
        connection = await aio_pika.connect_robust(rabbitmq_url)
        print(f"✅ [CONSUMER] Connected to RabbitMQ")
        
        # Создание канала
        print(f"🔵 [CONSUMER] Creating channel...")
        channel = await connection.channel()
        print(f"✅ [CONSUMER] Channel created")

        # Декларация exchange
        print(f"🔵 [CONSUMER] Declaring exchange 'user_events'...")
        exchange = await channel.declare_exchange(
            "user_events", type="direct", durable=True
        )
        print(f"✅ [CONSUMER] Exchange 'user_events' declared")

        # Декларация очереди
        print(f"🔵 [CONSUMER] Declaring queue 'user_profile_queue'...")
        queue = await channel.declare_queue("user_profile_queue", durable=True)
        print(f"✅ [CONSUMER] Queue 'user_profile_queue' declared")
        print(f"🔵 [CONSUMER] Queue details: {queue}")

        # Привязка очереди к exchange
        print(f"🔵 [CONSUMER] Binding queue to exchange with routing_key='user.created'...")
        await queue.bind(exchange, routing_key="user.created")
        print(f"✅ [CONSUMER] Queue bound successfully")

        print(f"\n✅ [CONSUMER] {'='*50}")
        print(f"✅ [CONSUMER] Waiting for user.created events...")
        print(f"✅ [CONSUMER] {'='*50}\n")

        # Начинаем прослушивание очереди
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # 👇 УБИРАЕМ `async with message.process()` - будем контролировать ack вручную
                max_retries = 3
                retry_count = 0
                processed = False
                
                while retry_count < max_retries and not processed:
                    try:
                        print(f"\n📨 [CONSUMER] {'='*50}")
                        print(f"📨 [CONSUMER] Processing message (attempt {retry_count + 1}/{max_retries})")
                        
                        # Получаем данные из сообщения
                        data = json.loads(message.body.decode())
                        print(f"📨 [CONSUMER] Body: {data}")
                        print(f"📨 [CONSUMER] Headers: {message.headers}")
                        print(f"📨 [CONSUMER] Routing key: {message.routing_key}")

                        user_id = data.get("user_id")
                        email = data.get("email", "")
                        username = data.get("username", "")
                        name = data.get("name", "")
                        role_raw = data.get("role", "")

                        print(f"🔵 [CONSUMER] Extracted data:")
                        print(f"  - user_id: {user_id}")
                        print(f"  - email: {email}")
                        print(f"  - username: {username}")
                        print(f"  - name: {name}")
                        print(f"  - role_raw: {role_raw}")

                        # Преобразуем роль
                        role_str = str(role_raw).lower()
                        print(f"🔵 [CONSUMER] Role string: {role_str}")
                        
                        if role_str not in ROLE_MAPPING:
                            print(f"❌ [CONSUMER] Unknown role: {role_raw}, user_id={user_id}")
                            await message.ack()
                            processed = True
                            continue

                        user_role = ROLE_MAPPING[role_str]
                        print(f"✅ [CONSUMER] Mapped role: {user_role}")

                        # Создаем профиль в БД
                        print(f"🔵 [CONSUMER] Connecting to database...")
                        async with async_session_maker() as session:
                            print(f"🔵 [CONSUMER] Checking if user {user_id} exists in profile DB...")
                            result = await session.execute(
                                select(User).where(User.id == user_id)
                            )
                            user = result.scalar_one_or_none()

                            if not user:
                                print(f"🔵 [CONSUMER] User {user_id} not found, creating profile...")
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
                                print(f"✅ [CONSUMER] Profile CREATED for user_id={user_id}")
                                print(f"✅ [CONSUMER] Profile details: id={new_profile.id}, username={new_profile.username}")
                            else:
                                print(f"✅ [CONSUMER] Profile already exists for user_id={user_id}")
                                print(f"✅ [CONSUMER] Existing profile: {user}")

                        # Сообщение обработано успешно
                        await message.ack()
                        print(f"✅ [CONSUMER] Message acknowledged")
                        processed = True
                        print(f"📨 [CONSUMER] {'='*50}\n")

                    except Exception as e:
                        retry_count += 1
                        print(f"❌ [CONSUMER] Error processing message (attempt {retry_count}/{max_retries}): {e}")
                        print(f"❌ [CONSUMER] Error type: {type(e)}")
                        import traceback
                        traceback.print_exc()
                        
                        if retry_count < max_retries:
                            # Ждем перед повторной попыткой
                            wait_time = retry_count * 2  # 2, 4, 6 секунд
                            print(f"⏳ [CONSUMER] Waiting {wait_time} seconds before retry...")
                            await asyncio.sleep(wait_time)
                        else:
                            # Исчерпали все попытки - не возвращаем в очередь
                            print(f"💔 [CONSUMER] Max retries ({max_retries}) reached, rejecting message")
                            await message.nack(requeue=False)
                            processed = True

    except Exception as e:
        print(f"❌ [CONSUMER] Fatal error in consumer: {e}")
        print(f"❌ [CONSUMER] Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise


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

                print(
                    f"[CONSUMER] Received role update for user {user_id}: {old_role} -> {new_role}"
                )

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
                        print(
                            f"[CONSUMER] Role updated for user_id={user_id} to {new_role}"
                        )
                    else:
                        print(f"[CONSUMER] User {user_id} not found")

                await message.ack()

            except Exception as e:
                print(f"[CONSUMER] Error processing message: {e}")
                await message.nack(requeue=False)
