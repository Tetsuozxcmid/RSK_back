import asyncio
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest

from routes.profile_routers.router import router
from services.rabbitmq import consume_user_created_events, consume_role_updated_events
from config import settings
from db.base import Base
from db.session import engine
from services.parser import org_parser
import aio_pika
import logging


SERVICE_NAME = "profile_service"

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "path"],
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

consumer_task = None
role_consumer_task = None
rabbitmq_connection = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_connection, consumer_task, role_consumer_task
    
    logger.info("=== STARTUP: Creating database tables ===")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("=== STARTUP: Parsing organizations ===")
    file_path = os.path.join(os.path.dirname(__file__), "rsk_orgs_list.xlsx")
    org_parser.parse_excel(file_path)

    logger.info("=== STARTUP: Connecting to RabbitMQ ===")
    try:
        rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        app.state.rabbitmq_connection = rabbitmq_connection
        logger.info("=== STARTUP: RabbitMQ connected ===")
    except Exception as e:
        logger.error(f"=== STARTUP: Failed to connect to RabbitMQ: {e} ===")
        raise

    logger.info("=== STARTUP: Starting RabbitMQ consumers ===")
    
    
    consumer_task = asyncio.create_task(
        consume_user_created_events(settings.RABBITMQ_URL)
    )
    
    
    role_consumer_task = asyncio.create_task(
        consume_role_updated_events(settings.RABBITMQ_URL)
    )

    def handle_task_result(task: asyncio.Task, consumer_name: str) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            logger.info(f"{consumer_name} was cancelled")
        except Exception as e:
            logger.error(f"{consumer_name} crashed: {e}")

    consumer_task.add_done_callback(
        lambda t: handle_task_result(t, "User created consumer")
    )
    role_consumer_task.add_done_callback(
        lambda t: handle_task_result(t, "Role updated consumer")
    )
    
    logger.info("=== STARTUP: RabbitMQ consumers started ===")

    yield

    logger.info("=== SHUTDOWN: Cancelling RabbitMQ consumers ===")
    if consumer_task:
        consumer_task.cancel()
    if role_consumer_task:
        role_consumer_task.cancel()
    
    try:
        await asyncio.gather(consumer_task, role_consumer_task, return_exceptions=True)
    except Exception as e:
        logger.error(f"Error during consumer shutdown: {e}")
    
    logger.info("=== SHUTDOWN: Closing RabbitMQ connection ===")
    if rabbitmq_connection:
        await rabbitmq_connection.close()
    
    logger.info("=== SHUTDOWN: Complete ===")


app = FastAPI(
    title="User Profile Service",
    root_path="/users",
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)

    duration = time.time() - start
    path = request.url.path

    REQUEST_COUNT.labels(
        SERVICE_NAME,
        request.method,
        path,
        response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        SERVICE_NAME,
        path,
    ).observe(duration)

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type="text/plain")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rabbitmq_connected": rabbitmq_connection is not None and not rabbitmq_connection.is_closed,
        "consumers": {
            "user_created": consumer_task is not None and not consumer_task.done(),
            "role_updated": role_consumer_task is not None and not role_consumer_task.done(),
        }
    }