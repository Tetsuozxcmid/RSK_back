from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.router import router
import importlib
import schemas.proj



app = FastAPI(title='Projects FASTAPI',description='xxx',root_path='/projects')
importlib.reload(schemas.proj)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

