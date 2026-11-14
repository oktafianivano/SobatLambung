from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.config import settings
from app.limiter import limiter, rate_limit_handler
from app.middleware import SecurityHeadersMiddleware
from app.scheduler import init_scheduler
from app.api.router import API_V1_PREFIX, api_legacy_router, api_v1_router

# Skema database dikelola oleh Alembic (lihat folder `alembic/`).
# create_all hanya dipakai untuk kenyamanan development/test; di production
# jalankan `alembic upgrade head` lebih dahulu (sudah otomatis di Dockerfile).
if settings.APP_ENV.lower() != "production":
    Base.metadata.create_all(bind=engine)


def _warn_insecure_settings() -> None:
    """Ingatkan (tanpa menghentikan app) jika konfigurasi masih lemah."""
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
    print("[INFO] APScheduler Sobat Lambung aktif (Jadwal: 07:30, 12:00, 18:30 WIB)")
    yield
    scheduler.shutdown()
    print("[INFO] APScheduler dimatikan")

app = FastAPI(
    title="Sobat Lambung API",
    description="Backend API Decoupled untuk Edukasi Gastritis/GERD & Pengingat Jam Makan WhatsApp",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting (slowapi): batas per IP, tanpa perlu membatasi CORS.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Security headers dipasang lebih dulu, lalu CORS di lapisan terluar agar
# header CORS tetap ada pada semua respons (termasuk error 429/4xx).
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def read_root():
    """Info singkat API di root (dipertahankan dari versi sebelumnya)."""
    return {
        "app": "Sobat Lambung API",
        "status": "online",
        "version": app.version,
        "api_base": API_V1_PREFIX,
        "docs_url": "/docs",
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Dipakai oleh monitoring / platform deploy untuk memastikan API hidup."""
    return {
        "status": "ok",
        "service": "sobat-lambung-api",
        "version": app.version,
        "env": settings.APP_ENV,
        "api_base": API_V1_PREFIX,
    }

app.include_router(api_v1_router)
# Alias lama (/api/...) tetap aktif agar klien versi sebelumnya tidak rusak.
app.include_router(api_legacy_router)
