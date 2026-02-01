from fastapi import FastAPI
from routes.org_route import router as orgs_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ORGS FASTAPI", description="xxx", root_path="/orgs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(orgs_router)
