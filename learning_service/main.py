from fastapi import FastAPI
from app.routes.coures_routes.route import router as courses_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Learning Service", version="1.0.0", root_path="/learning")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses_router)
