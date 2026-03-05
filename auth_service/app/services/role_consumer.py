import json
import aio_pika
from sqlalchemy.future import select
from db.models.user import User, UserRole
from db.session import async_session_maker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ROLE_MAPPING = {
    "student": UserRole.STUDENT,
    "teacher": UserRole.TEACHER,
    "moder": UserRole.MODER,
    "admin": UserRole.ADMIN,
}


async def consume_role_updated_events(rabbitmq_url: str):
    try:
        logger.info(f"[AUTH CONSUMER] Connecting to RabbitMQ at {rabbitmq_url}")
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        
        logger.info("[AUTH CONSUMER] Connected, declaring exchange and queue")
        
        exchange = await channel.declare_exchange(
            "user_events", type="direct", durable=True
        )
        
        queue = await channel.declare_queue("auth_role_queue", durable=True)
        await queue.bind(exchange, routing_key="user.role_updated")
        
        logger.info("[AUTH CONSUMER] Waiting for user.role_updated events...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        logger.info(f"[AUTH CONSUMER] Received message: {data}")
                        
                        user_id = data.get("user_id")
                        new_role = data.get("new_role")
                        old_role = data.get("old_role")

                        logger.info(
                            f"[AUTH CONSUMER] Processing role update for user {user_id}: {old_role} -> {new_role}"
                        )

                        role_str = str(new_role).lower()
                        if role_str not in ROLE_MAPPING:
                            logger.error(f"[AUTH CONSUMER] Unknown role: {new_role}")
                            continue

                        new_role_enum = ROLE_MAPPING[role_str]

                        async with async_session_maker() as session:
                            logger.info(f"[AUTH CONSUMER] Looking up user {user_id} in DB")
                            result = await session.execute(
                                select(User).where(User.id == user_id)
                            )
                            user = result.scalar_one_or_none()

                            if user:
                                old_db_role = user.role
                                user.role = new_role_enum
                                await session.commit()
                                logger.info(
                                    f"[AUTH CONSUMER] ✅ Role updated in auth DB for user {user_id}: {old_db_role} -> {new_role}"
                                )
                            else:
                                logger.error(
                                    f"[AUTH CONSUMER] ❌ User {user_id} not found in auth DB"
                                )

                    except Exception as e:
                        logger.error(f"[AUTH CONSUMER] Error processing message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[AUTH CONSUMER] Connection error: {e}", exc_info=True)
