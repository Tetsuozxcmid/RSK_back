import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest

from routes.coures_routes.route import router as courses_router
from routes.submissons_routes.route import router as submissions_router
from routes.moderator_assign.route import router as moderator_router
from services.assignement import assignment_service
from config import settings



SERVICE_NAME = "learning_service"

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "path"],
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await assignment_service.connect()
    yield
   
    await assignment_service.close()


app = FastAPI(
    title="Learning FASTAPI",
    description="xxx",
    root_path="/learning",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)

    duration = time.time() - start
    path = request.url.path

    REQUEST_COUNT.labels(
        SERVICE_NAME,
        request.method,
        path,
        response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        SERVICE_NAME,
        path,
    ).observe(duration)

    return response



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(courses_router, prefix="/api/courses", tags=["courses"])
app.include_router(submissions_router, prefix="/api/submissions", tags=["submissions"])
app.include_router(
    moderator_router,
    prefix="/api/moderator",
    tags=["moderator-assignments"],
)




@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type="text/plain")

