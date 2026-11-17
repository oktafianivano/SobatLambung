from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.scheduler import init_scheduler
from app.api.endpoints import public, auth, users, admin

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = init_scheduler()
    scheduler.start()
    print(f"🚀 APScheduler Sobat Lambung aktif (Jadwal: 09:55, 12:00, 18:30 WIB)")
    yield
    scheduler.shutdown()
    print("🛑 APScheduler dimatikan")

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

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=DEV_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router, tags=["Public"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(users.router, prefix="/api/user", tags=["User Dashboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Tools"])