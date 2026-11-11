from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.config import settings
from app.scheduler import init_scheduler
from app.api.router import API_V1_PREFIX, api_legacy_router, api_v1_router

# Skema database dikelola oleh Alembic (lihat folder `alembic/`).
# create_all hanya dipakai untuk kenyamanan development/test; di production
# jalankan `alembic upgrade head` lebih dahulu (sudah otomatis di Dockerfile).
if settings.APP_ENV.lower() != "production":
    Base.metadata.create_all(bind=engine)

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