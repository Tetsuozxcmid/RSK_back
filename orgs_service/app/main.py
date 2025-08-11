from fastapi import FastAPI
from routes.org_route import router as orgs_router

app = FastAPI(title="FastAPI", description="xxx", docs_url="/")
app.include_router(orgs_router)
