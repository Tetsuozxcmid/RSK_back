from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.users_router.router import router as user_router
from services.rabbitmq import init_rabbitmq

app = FastAPI(title="Auth FASTAPI", description="xxx", root_path="/auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)


@app.on_event("startup")
async def startup():
    await init_rabbitmq()
