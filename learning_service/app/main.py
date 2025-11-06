from fastapi import FastAPI
from routes.coures_routes.route import router as courses_router
from routes.submissons_routes.route import router as submissions_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title='Learning FASTAPI',
    description='xxx',
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем /learning в префикс каждого роутера
app.include_router(courses_router, prefix="/learning/api/courses", tags=["courses"])
app.include_router(submissions_router, prefix="/learning/api/submissions", tags=["submissions"])
