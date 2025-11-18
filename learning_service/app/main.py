import os
from fastapi import FastAPI
from routes.coures_routes.route import router as courses_router
from routes.submissons_routes.route import router as submissions_router
from routes.moderator_assign.route import router as moderator_router
from fastapi.middleware.cors import CORSMiddleware
from services.assignement import assignment_service
from config import settings

app = FastAPI(title="Learning FASTAPI", description="xxx", root_path="/learning",openapi_url="/openapi.json")
#Для локалки
#app = FastAPI(
    #title="Learning FASTAPI", 
    #description="xxx",
    #docs_url="/learning/docs",
    #redoc_url="/learning/redoc",
    #openapi_url="/learning/openapi.json"
#)

#для прода
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    redis_url = settings.REDIS_URL
    await assignment_service.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await assignment_service.close()

app.include_router(courses_router, prefix="/api/courses", tags=["courses"])
app.include_router(submissions_router, prefix="/api/submissions", tags=["submissions"])
app.include_router(moderator_router, prefix="/api/moderator", tags=["moderator-assignments"]) 
