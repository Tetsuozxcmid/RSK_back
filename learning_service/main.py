from fastapi import FastAPI
from app.routes.coures_routes.route import router as courses_router

app = FastAPI(title="Learning Service", version="1.0.0")

app.include_router(courses_router)
