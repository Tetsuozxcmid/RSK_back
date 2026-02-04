
from prometheus_client import Counter, Histogram, Gauge


SERVICE_NAME = "auth_service"


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "path"]
)


ACTIVE_USERS = Gauge(
    "active_users_total",
    "Total active users",
    ["service"]
)