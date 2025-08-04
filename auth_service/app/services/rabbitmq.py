
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from config import settings

rabbitmq_connection: AbstractRobustConnection = None

async def get_rabbitmq_connection() -> AbstractRobustConnection:
    if not rabbitmq_connection:
        raise RuntimeError("RabbitMQ connection not initialized")
    return rabbitmq_connection

async def init_rabbitmq():
    global rabbitmq_connection
    rabbitmq_connection = await aio_pika.connect_robust(
        settings.RABBITMQ_URL  
    )
    print("RabbitMQ connection established")