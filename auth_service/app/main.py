from fastapi import FastAPI

from routes.users_router.router import router as user_router
from services.rabbitmq import init_rabbitmq

app = FastAPI(title='FastAPI',description='xxx',docs_url='/')


app.include_router(user_router)

@app.on_event("startup")
async def startup():
    await init_rabbitmq()