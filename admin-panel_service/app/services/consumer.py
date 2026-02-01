import aio_pika
import json

from config import settings
from handlers.projects import handle as project_handler


class RabbitMQConsumer:
    def __init__(self):
        self.url: str = settings.RABBIT_URL

        self.connection: aio_pika.Connection | None = None
        self.channel: aio_pika.Channel | None = None
        self.exchange: aio_pika.Exchange | None = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(url=self.url)
        self.channel = await self.connection.channel()

        self.exchange = await self.channel.declare_exchange(
            name="admin.commands", type=aio_pika.ExchangeType.TOPIC, durable=True
        )

        self.queue = await self.channel.declare_queue(
            name="admin.commands.queue", durable=True
        )

        await self.queue.bind(exchange=self.exchange, routing_key="projects.*")
        await self.queue.bind(exchange=self.exchange, routing_key="teachers.*")

    async def handle_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process():
            data = json.loads(message.body.decode())
            routing_key = message.routing_key

            if routing_key is None:
                return

            if routing_key.startswith("projects"):
                await project_handler(data=data)
