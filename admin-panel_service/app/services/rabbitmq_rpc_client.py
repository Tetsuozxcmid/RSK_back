
import asyncio
import uuid
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.config import settings

class RabbitMQRPCClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.futures = {}
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        self.connection = await aio_pika.connect_robust(settings.RABBIT_URL)
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response)

    async def on_response(self, message: AbstractIncomingMessage):
        future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def call(self, routing_key: str, message: dict) -> Any:
        if not self.connection:
            await self.connect()

        correlation_id = str(uuid.uuid4())
        future = self.loop.create_future()

        self.futures[correlation_id] = future

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message,
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=routing_key,
        )

        return await future
