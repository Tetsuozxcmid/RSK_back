from fastapi import FastAPI
from app.routes.videos import router as videos_router
from app.routes.courses import router as courses_router

app = FastAPI(title="Learning Service", version="1.0.0")

app.include_router(videos_router)
app.include_router(courses_router)


def main():
    print("Hello from learning-service!")


if __name__ == "__main__":
    main()