from fastapi import FastAPI
from routes.teams_router.router import router as team_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='FastAPI',description='xxx',docs_url='/')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(team_router)