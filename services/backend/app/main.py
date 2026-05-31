from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import make_asgi_app

from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, devices, rules, logs, alerts, dashboard, system
from app.websockets.dashboard import realtime_feed

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="AntiGravity Shield API",
    description="Centralized ad-blocking and network management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Routers
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(rules.router)
app.include_router(logs.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(system.router)


# WebSocket
@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    await realtime_feed(websocket)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "antigravity-shield-api"}
