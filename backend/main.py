from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.config import settings
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    """Dipakai oleh monitoring / platform deploy untuk memastikan API hidup."""
    return {
        "status": "ok",
        "service": "sobat-lambung-api",
        "version": app.version,
        "env": settings.APP_ENV,
    }

app.include_router(public.router, tags=["Public"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(users.router, prefix="/api/user", tags=["User Dashboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Tools"])