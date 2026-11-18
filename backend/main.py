from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.config import settings
from app.limiter import limiter, rate_limit_handler
from app.middleware import SecurityHeadersMiddleware
from app.scheduler import init_scheduler
from app.reminder_config import MEAL_ORDER, reminder_config
from app.api.router import API_V1_PREFIX, api_legacy_router, api_v1_router

if settings.APP_ENV.lower() != "production":
    Base.metadata.create_all(bind=engine)


def _warn_insecure_settings() -> None:
    if len(settings.SECRET_KEY) < 32:
        print(
            "[SECURITY WARNING] SECRET_KEY kurang dari 32 karakter. "
            "Gunakan nilai acak panjang, mis. `python -c \"import secrets;print(secrets.token_urlsafe(48))\"`."
        )
    if settings.ADMIN_API_KEY == "sobatlambung_it_2026":
        print(
            "[SECURITY WARNING] ADMIN_API_KEY masih memakai nilai default. "
            "Ganti dengan kunci acak sebelum aplikasi dipakai publik."
        )

_warn_insecure_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = init_scheduler()
    scheduler.start()
    jadwal = ", ".join(reminder_config.meal_times[meal] for meal in MEAL_ORDER)
    print(
        "[INFO] APScheduler Sobat Lambung aktif "
        f"(Jadwal: {jadwal} {reminder_config.timezone_label})"
    )
    yield
    scheduler.shutdown()
    print("[INFO] APScheduler dimatikan")

app = FastAPI(
    title="Sobat Lambung API",
    description="Backend API Decoupled untuk Edukasi Gastritis/GERD & Pengingat Jam Makan WhatsApp",
    version="1.0.0",
    lifespan=lifespan
)

# Izinkan origin development: localhost + semua IP privat (LAN) di port berapa pun.
# Ini mencegah error "Failed to fetch"/CORS saat IP perangkat berubah-ubah.
DEV_ORIGIN_REGEX = (
    r"^https?://("
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
    r")(:\d+)?$"
)

# Origin tambahan dari .env (CORS_ORIGINS), mis. domain tunnel/produksi.
configured_origins = [
    origin for origin in settings.cors_origins_list if origin != "*"
]

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_origin_regex=DEV_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def read_root():
    return {
        "app": "Sobat Lambung API",
        "status": "online",
        "version": app.version,
        "api_base": API_V1_PREFIX,
        "docs_url": "/docs",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "sobat-lambung-api",
        "version": app.version,
        "env": settings.APP_ENV,
        "api_base": API_V1_PREFIX,
    }

app.include_router(api_v1_router)
app.include_router(api_legacy_router)
