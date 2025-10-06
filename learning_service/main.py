from fastapi import FastAPI
from app.routes.coures_routes.route import router as courses_router
from learning_service.app.routes.submissons_routes.route import router as submissions_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Learning Service", version="1.0.0", docs_url="/learning/docs", openapi_url="/learning/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses_router, prefix="/learning")
app.include_router(submissions_router, prefix="/learning")
