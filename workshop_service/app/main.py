from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Test FastAPI App", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Hello World!", "status": "OK"}


