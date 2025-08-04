import asyncio
from fastapi import FastAPI
from routes.profile_routers.router import router
from services.rabbitmq import consume_user_created_events
from config import settings
from db.base import Base
from db.session import engine

app = FastAPI(title='User Profile Service', docs_url='/')

app.include_router(router)

@app.on_event("startup")
async def startup():
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    
    loop = asyncio.get_event_loop()
    task = loop.create_task(consume_user_created_events(settings.RABBITMQ_URL))
    
    
    def handle_task_result(task: asyncio.Task) -> None:
        try:
            task.result()
        except Exception as e:
            print(f"RabbitMQ consumer crashed: {e}")
            

    task.add_done_callback(handle_task_result)