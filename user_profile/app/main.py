import asyncio
import os
from fastapi import FastAPI
from routes.profile_routers.router import router
from services.rabbitmq import consume_user_created_events
from config import settings
from db.base import Base
from db.session import engine
from fastapi.middleware.cors import CORSMiddleware
from services.parser import org_parser

app = FastAPI(title='User Profile Service', root_path='/users')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup():
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    file_path = os.path.join(os.path.dirname(__file__),"rsk_orgs_list.xlsx")
    org_parser.parse_excel(file_path)
    

    
    loop = asyncio.get_event_loop()
    task = loop.create_task(consume_user_created_events(settings.RABBITMQ_URL))
    
    
    def handle_task_result(task: asyncio.Task) -> None:
        try:
            task.result()
        except Exception as e:
            print(f"RabbitMQ consumer crashed: {e}")
            

    task.add_done_callback(handle_task_result)
