from app.routes.projects import router as projects_router
from app.routes.tasks import router as tasks_router
from app.routes.teachers import router as teachers_router

from fastapi import FastAPI

app = FastAPI()

app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(teachers_router)
