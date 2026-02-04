
from prometheus_client import Counter, Histogram, Gauge


SERVICE_NAME = "auth_service"




ACTIVE_USERS = Gauge(
    "active_users_total",
    "Total active users",
    ["service"]
)