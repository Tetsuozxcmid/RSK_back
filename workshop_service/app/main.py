import asyncio
from fastapi import FastAPI

from config import settings
from db.base import Base
from db.session import engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='WorkShop Service', docs_url='/')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

