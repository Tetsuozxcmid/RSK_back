import asyncio
import json
import logging
from datetime import datetime

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from fastapi import Request
from sqlalchemy import select

from cruds.profile_crud import ProfileCRUD
from db.models.user import User
from db.models.user_enum import UserEnum
from db.session import async_session_maker
from schemas.user import OAuthProfileSyncRequest


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
        logger.info(
            "[PUBLISHER] Attempting to publish role update for user %s: %s -> %s",
            user_id,
            old_role,
            new_role,
        )

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
        logger.info(
            "[PUBLISHER] Role update published for user %s: %s -> %s",
            user_id,
            old_role,
            new_role,
        )

    except Exception as e:
        logger.error("[PUBLISHER] Failed to publish role update: %s", e, exc_info=True)
        raise


async def consume_user_created_events(rabbitmq_url: str):
    logger.info("[CONSUMER] Starting user.created consumer")

    try:
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "user_events", type="direct", durable=True
        )
        queue = await channel.declare_queue("user_profile_queue", durable=True)
        await queue.bind(exchange, routing_key="user.created")

        logger.info("[CONSUMER] Waiting for user.created events")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                max_retries = 3
                retry_count = 0
                processed = False

                while retry_count < max_retries and not processed:
                    try:
                        data = json.loads(message.body.decode())
                        logger.info("[CONSUMER] Processing user.created payload: %s", data)

                        user_id = data.get("user_id")
                        if not user_id:
                            logger.warning("[CONSUMER] Missing user_id in payload: %s", data)
                            await message.ack()
                            processed = True
                            continue

                        async with async_session_maker() as session:  # type: ignore
                            sync_result = await ProfileCRUD.sync_oauth_profile(
                                db=session,
                                sync_data=OAuthProfileSyncRequest(
                                    user_id=user_id,
                                    email=data.get("email", ""),
                                    username=data.get("username", ""),
                                    first_name=data.get("first_name"),
                                    last_name=data.get("last_name"),
                                    patronymic=data.get("patronymic"),
                                    full_name=data.get("full_name") or data.get("name"),
                                    role=data.get("role"),
                                    auth_provider=data.get("auth_provider"),
                                ),
                            )

                        logger.info(
                            "[CONSUMER] Profile sync result for user_id=%s: %s",
                            user_id,
                            sync_result,
                        )
                        await message.ack()
                        processed = True

                    except Exception as e:
                        retry_count += 1
                        logger.error(
                            "[CONSUMER] Error processing user.created (attempt %s/%s): %s",
                            retry_count,
                            max_retries,
                            e,
                            exc_info=True,
                        )

                        if retry_count < max_retries:
                            await asyncio.sleep(retry_count * 2)
                        else:
                            await message.nack(requeue=False)
                            processed = True

    except Exception as e:
        logger.error("[CONSUMER] Fatal error in user.created consumer: %s", e, exc_info=True)
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

    logger.info("[CONSUMER] Waiting for user.role_updated events")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                data = json.loads(message.body.decode())

                user_id = data.get("user_id")
                new_role = data.get("new_role")
                old_role = data.get("old_role")

                logger.info(
                    "[CONSUMER] Received role update for user %s: %s -> %s",
                    user_id,
                    old_role,
                    new_role,
                )

                role_str = str(new_role).lower()
                if role_str not in ROLE_MAPPING:
                    logger.warning(
                        "[CONSUMER] Unknown role %s for user_id=%s",
                        new_role,
                        user_id,
                    )
                    await message.ack()
                    continue

                new_role_enum = ROLE_MAPPING[role_str]

                async with async_session_maker() as session:  # type: ignore
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()

                    if user:
                        user.Type = new_role_enum
                        await session.commit()
                        logger.info(
                            "[CONSUMER] Role updated for user_id=%s to %s",
                            user_id,
                            new_role,
                        )
                    else:
                        logger.warning("[CONSUMER] User %s not found", user_id)

                await message.ack()

            except Exception as e:
                logger.error(
                    "[CONSUMER] Error processing user.role_updated: %s",
                    e,
                    exc_info=True,
                )
                await message.nack(requeue=False)
