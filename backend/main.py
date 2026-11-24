
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.config import settings
from app.limiter import limiter, rate_limit_handler
from app.middleware import SecurityHeadersMiddleware
from app.scheduler import init_scheduler
from app.reminder_config import MEAL_ORDER, reminder_config
from app.api.router import (
    API_V1_PREFIX,
    api_legacy_router,
    api_v1_router,
)


logger = logging.getLogger("sobat_lambung")

IS_PRODUCTION = settings.APP_ENV.lower() == "production"


# Database initialization
if not IS_PRODUCTION:
    Base.metadata.create_all(bind=engine)


# CORS configuration
DEV_ORIGIN_REGEX = (
    r"^https?://("
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
    r")(:\d+)?$"
)

configured_origins = [
    origin.strip().rstrip("/")
    for origin in settings.cors_origins_list
    if origin.strip() and origin.strip() != "*"
]


if IS_PRODUCTION:
    if not configured_origins:
        raise RuntimeError(
            "CORS_ORIGINS must be configured in production."
        )

    if any(
        not origin.startswith("https://")
        for origin in configured_origins
    ):
        raise RuntimeError(
            "Production CORS origins must use HTTPS."
        )


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = init_scheduler()
    scheduler.start()

    jadwal = ", ".join(
        reminder_config.meal_times[meal]
        for meal in MEAL_ORDER
    )

    logger.info(
        "APScheduler Sobat Lambung aktif. Jadwal: %s %s",
        jadwal,
        reminder_config.timezone_label,
    )

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)

        logger.info("APScheduler dimatikan.")


# FastAPI application
app = FastAPI(
    title="Sobat Lambung API",
    description=(
        "Backend API Decoupled untuk Edukasi Gastritis/GERD "
        "& Pengingat Jam Makan WhatsApp"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)


# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_handler,
)


# Security headers
app.add_middleware(SecurityHeadersMiddleware)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_origin_regex=(
        None if IS_PRODUCTION else DEV_ORIGIN_REGEX
    ),
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
        "HEAD",
    ],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
        "X-Requested-With",
    ],
)


# Health endpoints
@app.get("/", tags=["Health"])
def read_root():
    return {
        "app": "Sobat Lambung API",
        "status": "online",
        "version": app.version,
        "api_base": API_V1_PREFIX,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "sobat-lambung-api",
        "version": app.version,
    }


# API routers
app.include_router(api_v1_router)
app.include_router(api_legacy_router)
