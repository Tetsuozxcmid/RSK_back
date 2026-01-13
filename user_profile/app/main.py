import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.profile_routers.router import router
from services.rabbitmq import consume_user_created_events
from config import settings
from db.base import Base
from db.session import engine
from fastapi.middleware.cors import CORSMiddleware
from services.parser import org_parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=== STARTUP: Creating database tables ===")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("=== STARTUP: Parsing organizations ===")
    file_path = os.path.join(os.path.dirname(__file__), "rsk_orgs_list.xlsx")
    org_parser.parse_excel(file_path)

    logger.info("=== STARTUP: Starting RabbitMQ consumer ===")
    global consumer_task
    consumer_task = asyncio.create_task(consume_user_created_events(settings.RABBITMQ_URL))
    
    def handle_task_result(task: asyncio.Task) -> None:
        try:
            task.result()
        except Exception as e:
            logger.error(f"RabbitMQ consumer crashed: {e}")

    consumer_task.add_done_callback(handle_task_result)
    logger.info("=== STARTUP: RabbitMQ consumer started ===")
    
    yield
    
    # Shutdown
    logger.info("=== SHUTDOWN: Cancelling RabbitMQ consumer ===")
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    logger.info("=== SHUTDOWN: Complete ===")

app = FastAPI(
    title='User Profile Service', 
    root_path='/users',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "consumer_running": consumer_task is not None and not consumer_task.done()}
