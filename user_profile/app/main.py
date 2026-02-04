import asyncio
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest

from routes.profile_routers.router import router
from services.rabbitmq import consume_user_created_events
from config import settings
from db.base import Base
from db.session import engine
from services.parser import org_parser
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== STARTUP: Creating database tables ===")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("=== STARTUP: Parsing organizations ===")
    file_path = os.path.join(os.path.dirname(__file__), "rsk_orgs_list.xlsx")
    org_parser.parse_excel(file_path)

    logger.info("=== STARTUP: Starting RabbitMQ consumer ===")
    global consumer_task
    consumer_task = asyncio.create_task(
        consume_user_created_events(settings.RABBITMQ_URL)
    )

    def handle_task_result(task: asyncio.Task) -> None:
        try:
            task.result()
        except Exception as e:
            logger.error(f"RabbitMQ consumer crashed: {e}")

    consumer_task.add_done_callback(handle_task_result)
    logger.info("=== STARTUP: RabbitMQ consumer started ===")

    yield

    logger.info("=== SHUTDOWN: Cancelling RabbitMQ consumer ===")
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
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
        "consumer_running": consumer_task is not None and not consumer_task.done(),
    }
