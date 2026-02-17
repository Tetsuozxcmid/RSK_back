from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import time
import asyncio
from sqlalchemy import select, func

from config import settings
from routes.users_router.router import router as user_router
from services.rabbitmq import init_rabbitmq
from services.role_consumer import consume_role_updated_events  
from db.session import async_session_maker
from db.models.user import User


SERVICE_NAME = "auth_service"

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["service", "path"]
)

ACTIVE_USERS = Gauge("active_users_total", "Total verified users", ["service"])

TOTAL_USERS = Gauge("total_users", "Total registered users", ["service"])


metrics_task = None
role_consumer_task = None
rabbitmq_connection = None


async def update_metrics_periodically():
    while True:
        try:
            async with async_session_maker() as session:
                stmt_verified = select(func.count()).where(User.verified == True)
                result = await session.execute(stmt_verified)
                verified_count = result.scalar() or 0

                stmt_total = select(func.count()).select_from(User)
                result_total = await session.execute(stmt_total)
                total_count = result_total.scalar() or 0

                ACTIVE_USERS.labels(service=SERVICE_NAME).set(verified_count)
                TOTAL_USERS.labels(service=SERVICE_NAME).set(total_count)

                print(
                    f"Metrics updated: verified={verified_count}, total={total_count}"
                )

        except Exception as e:
            print(f"Error updating metrics: {e}")

        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global metrics_task, role_consumer_task, rabbitmq_connection
    
    print("Starting auth service...")
    
   
    rabbitmq_connection = await init_rabbitmq()
    app.state.rabbitmq_connection = rabbitmq_connection
    
    
    print("Starting RabbitMQ role consumer...")
    role_consumer_task = asyncio.create_task(
        consume_role_updated_events(settings.RABBITMQ_URL)
    )

    
    metrics_task = asyncio.create_task(update_metrics_periodically())

   
    try:
        async with async_session_maker() as session:
            stmt = select(func.count()).where(User.verified == True)
            result = await session.execute(stmt)
            initial_count = result.scalar() or 0

            ACTIVE_USERS.labels(service=SERVICE_NAME).set(initial_count)
            TOTAL_USERS.labels(service=SERVICE_NAME).set(0)

            print(f"Initial metrics set: {initial_count} verified users")
    except Exception as e:
        print(f"Could not set initial metrics: {e}")

    print("Service started successfully")

    yield

    print("Shutting down auth service...")
    
    
    if role_consumer_task:
        role_consumer_task.cancel()
        try:
            await role_consumer_task
        except asyncio.CancelledError:
            pass
    
    
    if metrics_task:
        metrics_task.cancel()
        try:
            await metrics_task
        except asyncio.CancelledError:
            pass
    
   
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        await rabbitmq_connection.close()
        print("RabbitMQ connection closed")
    
    print("Service shutdown complete")


app = FastAPI(
    title="Auth FASTAPI",
    description="Authentication service",
    lifespan=lifespan,
    root_path="/auth",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
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


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type="text/plain")


@app.get("/health")
async def health():
    
    consumer_status = "running" if role_consumer_task and not role_consumer_task.done() else "stopped"
    rabbitmq_status = "connected" if rabbitmq_connection and not rabbitmq_connection.is_closed else "disconnected"
    
    return {
        "status": "healthy",
        "service": "auth",
        "consumers": {
            "role_consumer": consumer_status,
            "rabbitmq": rabbitmq_status
        },
        "metrics": {
            "verified_users": "active_users_total",
            "total_users": "total_users",
            "http_requests": "http_requests_total",
        },
    }


app.include_router(user_router)



@app.get("/update-metrics-now")
async def update_metrics_now():
    try:
        async with async_session_maker() as session:
            stmt_verified = select(func.count()).where(User.verified == True)
            result = await session.execute(stmt_verified)
            verified_count = result.scalar() or 0

            stmt_total = select(func.count())
            result_total = await session.execute(stmt_total)
            total_count = result_total.scalar() or 0

            ACTIVE_USERS.labels(service=SERVICE_NAME).set(verified_count)
            TOTAL_USERS.labels(service=SERVICE_NAME).set(total_count)

            return {
                "success": True,
                "verified_users": verified_count,
                "total_users": total_count,
                "message": f"Metrics updated: {verified_count} verified, {total_count} total",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}