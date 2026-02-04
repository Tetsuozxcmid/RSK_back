import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest

from routes.router import router



SERVICE_NAME = "projects_service"

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



app = FastAPI(
    title="Projects FASTAPI",
    description="xxx",
    root_path="/projects",
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

app.include_router(router)



@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type="text/plain")


