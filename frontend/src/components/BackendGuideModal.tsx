import React, { useState } from 'react';
import { Terminal, Copy, Check, FolderTree, Code2, Server, CheckCircle2, ChevronRight, FileCode } from 'lucide-react';

export const BackendGuideModal: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'terminal' | 'structure' | 'code'>('terminal');
  const [activeFile, setActiveFile] = useState<
    'requirements.txt' | '.env' | 'config.py' | 'database.py' | 'models.py' | 'auth.py' | 'scheduler.py' | 'main.py'
  >('models.py');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const fileContents = {
    'requirements.txt': `fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.35
pydantic>=2.9.0
pydantic-settings>=2.5.0
python-dotenv>=1.0.1
pyjwt[crypto]>=2.9.0
bcrypt>=4.0.1
pwdlib[argon2,bcrypt]>=0.2.1
apscheduler>=3.10.4
httpx>=0.27.2`,

    '.env': `# ========================================================
# SOBAT LAMBUNG - BACKEND ENVIRONMENT VARIABLES (.env)
# ========================================================

# Pengaturan Aplikasi & JWT Secret
APP_ENV=development
SECRET_KEY=sobat_lambung_super_secret_jwt_key_2026_xyz123abc
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database URL (SQLite untuk testing lokal)
DATABASE_URL=sqlite:///./sobat_lambung.db

# WhatsApp Gateway API (Fonnte)
# Dapatkan token perangkat dari dashboard https://fonnte.com
FONNTE_TOKEN=YOUR_FONNTE_TOKEN_HERE
FONNTE_API_URL=https://api.fonnte.com/send`,

    'config.py': `"""
Konfigurasi lingkungan dan pengaturan aplikasi Sobat Lambung.
Menggunakan Pydantic Settings untuk memuat variabel dari file .env secara otomatis.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "sobat_lambung_super_secret_jwt_key_2026_xyz123abc"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database URL
    DATABASE_URL: str = "sqlite:///./sobat_lambung.db"

    # WhatsApp Gateway Fonnte
    FONNTE_TOKEN: str = "YOUR_FONNTE_TOKEN_HERE"
    FONNTE_API_URL: str = "https://api.fonnte.com/send"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()`,

    'database.py': `"""
Konfigurasi koneksi database SQLAlchemy untuk Sobat Lambung.
Mendukung SQLite lokal dan dapat dialihkan ke MySQL tanpa mengubah logika aplikasi.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

# Argumen khusus SQLite agar thread FastAPI dapat berbagi koneksi
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Pembuat sesi database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk declarative models
Base = declarative_base()


def get_db():
    """
    Dependency injection generator untuk sesi database pada route FastAPI.
    Menjamin sesi selalu ditutup setelah request selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()`,

    'models.py': `"""
Model ORM SQLAlchemy untuk database Sobat Lambung.
Mendefinisikan skema tabel 'users' sesuai spesifikasi PRD.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    Model tabel 'users' untuk menyimpan data pengguna mahasiswa:
    - id: Primary Key unik autoincrement
    - nama: Nama lengkap mahasiswa
    - no_wa: Nomor WhatsApp (digunakan untuk login dan tujuan broadcast pengingat)
    - password_hash: Kata sandi yang telah dienkripsi dengan bcrypt / hashing aman
    - is_alarm_active: Status sakelar toggle pengingat WhatsApp (default True)
    - created_at: Waktu registrasi
    - updated_at: Waktu perubahan terakhir
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nama = Column(String(100), nullable=False)
    no_wa = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_alarm_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, nama='{self.nama}', no_wa='{self.no_wa}', is_alarm_active={self.is_alarm_active})>"`,

    'auth.py': `from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None`,

    'scheduler.py': `import logging
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from models import User
from config import settings

logger = logging.getLogger("sobat_lambung_scheduler")

MEAL_TEMPLATES = {
    "breakfast": {
        "title": "🌅 Waktunya Sarapan Sehat (06:30 WIB)",
        "menu": ["Bubur ayam kuah gurih ringan", "Oatmeal pisang & madu", "Roti gandum + telur rebus"],
        "advice": "Asam lambung pagi hari wajib dinetralisir sarapan rendah asam."
    },
    "lunch": {
        "title": "☀️ Waktunya Makan Siang (12:00 WIB)",
        "menu": ["Nasi pulen + sup wortel bayam + ayam kukus", "Ikan bumbu kunyit + tahu kukus"],
        "advice": "Kunyah perlahan, hindari kopi dingin & gorengan pedas kantin."
    },
    "dinner": {
        "title": "🌙 Waktunya Makan Malam (18:30 WIB)",
        "menu": ["Sup labu siam hangat + tempe bacem panggang", "Nasi tim ayam jamur"],
        "advice": "Beri jeda minimal 2-3 jam sebelum tidur untuk mencegah reflux GERD."
    }
}

def trigger_scheduled_broadcast(meal_key: str):
    db = SessionLocal()
    try:
        active_users = db.query(User).filter(User.is_alarm_active == True).all()
        for user in active_users:
            tpl = MEAL_TEMPLATES[meal_key]
            msg = f"Halo {user.nama}! Pengingat {tpl['title']}"
            # Kirim via Fonnte Gateway API
            # httpx.post(settings.FONNTE_API_URL, headers={"Authorization": settings.FONNTE_TOKEN}, ...)
    finally:
        db.close()`,

    'main.py': `from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, get_db
from models import User
from auth import hash_password, verify_password, create_access_token
from scheduler import init_scheduler

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Sobat Lambung API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return {"status": "online", "app": "Sobat Lambung"}`,
  };

  return (
    <section className="space-y-6">
      <div className="border-b border-slate-200 pb-5">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100 px-2.5 py-1 rounded-full mb-1">
          <Terminal className="w-3.5 h-3.5" />
          Panduan Pengembang & Arsitektur Decoupled
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
          Fondasi Backend FastAPI (Python 3.13) & SQLite
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          Langkah demi langkah memulai project di VS Code (OS Windows), virtual environment, struktur folder, dan kode sumber.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 max-w-xl">
        <button
          onClick={() => setActiveTab('terminal')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
            activeTab === 'terminal'
              ? 'bg-white text-indigo-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Terminal className="w-4 h-4 text-indigo-600" />
          Perintah Terminal (Windows)
        </button>

        <button
          onClick={() => setActiveTab('structure')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
            activeTab === 'structure'
              ? 'bg-white text-indigo-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <FolderTree className="w-4 h-4 text-indigo-600" />
          Struktur Folder
        </button>

        <button
          onClick={() => setActiveTab('code')}
          className={`flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
            activeTab === 'code'
              ? 'bg-white text-indigo-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Code2 className="w-4 h-4 text-indigo-600" />
          Kode Sumber Backend
        </button>
      </div>

      {/* Content 1: Terminal */}
      {activeTab === 'terminal' && (
        <div className="space-y-6">
          <div className="bg-slate-900 text-slate-100 rounded-2xl p-6 font-mono text-xs sm:text-sm shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-indigo-400 font-bold flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Terminal VS Code (OS Windows - PowerShell & CMD)
              </span>
              <button
                onClick={() =>
                  copyToClipboard(
                    `# 1. Buka folder project di VS Code\ncd sobat-lambung\n\n# 2. Buat Virtual Environment dengan Python 3.13\npy -3.13 -m venv venv\n\n# 3. Aktifkan Virtual Environment\n# Jika menggunakan PowerShell:\n.\\venv\\Scripts\\Activate.ps1\n\n# Jika menggunakan Command Prompt (CMD):\n.\\venv\\Scripts\\activate.bat\n\n# 4. Instalasi dependencies\ncd backend\npip install -r requirements.txt\n\n# 5. Jalankan server backend FastAPI\nuvicorn main:app --reload --port 8000`,
                    'all-terminal'
                  )
                }
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                {copiedKey === 'all-terminal' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey === 'all-terminal' ? 'Tersalin!' : 'Salin Perintah'}</span>
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-slate-400 text-xs">// Langkah 1: Buat Virtual Environment dengan Python 3.13</p>
                <div className="p-2.5 bg-slate-950 rounded-lg text-emerald-400">
                  py -3.13 -m venv venv
                </div>
              </div>

              <div>
                <p className="text-slate-400 text-xs">// Langkah 2: Aktifkan Virtual Environment di Windows</p>
                <p className="text-amber-300/80 text-[11px] mb-1">Opsi A (PowerShell):</p>
                <div className="p-2.5 bg-slate-950 rounded-lg text-emerald-400 mb-1">
                  .\venv\Scripts\Activate.ps1
                </div>
                <p className="text-[11px] text-slate-400 mb-1">
                  *Catatan: Jika muncul error "execution of scripts is disabled", jalankan: <code className="text-indigo-300">Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass</code>
                </p>
                <p className="text-amber-300/80 text-[11px] mt-2 mb-1">Opsi B (Command Prompt / CMD):</p>
                <div className="p-2.5 bg-slate-950 rounded-lg text-emerald-400">
                  .\venv\Scripts\activate.bat
                </div>
              </div>

              <div>
                <p className="text-slate-400 text-xs">// Langkah 3: Masuk ke folder backend & instal dependensi</p>
                <div className="p-2.5 bg-slate-950 rounded-lg text-emerald-400">
                  cd backend<br />
                  pip install -r requirements.txt
                </div>
              </div>

              <div>
                <p className="text-slate-400 text-xs">// Langkah 4: Jalankan server FastAPI</p>
                <div className="p-2.5 bg-slate-950 rounded-lg text-emerald-400">
                  uvicorn main:app --reload --port 8000
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  API Docs otomatis tersedia di: <span className="text-cyan-400">http://127.0.0.1:8000/docs</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content 2: Folder Structure */}
      {activeTab === 'structure' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <FolderTree className="w-5 h-5 text-indigo-600" />
              Struktur Proyek Arsitektur Decoupled (Frontend & Backend Terpisah)
            </h3>
            <button
              onClick={() =>
                copyToClipboard(
                  `sobat-lambung/
├── venv/                       # Virtual environment Python 3.13
├── backend/                    # Server-side (Python / FastAPI)
│   ├── .env                    # Variabel environment (Fonnte token, JWT secret)
│   ├── requirements.txt        # Dependensi Python
│   ├── config.py               # Pengaturan pydantic-settings
│   ├── database.py             # Koneksi SQLAlchemy & engine SQLite
│   ├── models.py               # Model ORM tabel Users
│   ├── schemas.py              # Pydantic validation schemas
│   ├── auth.py                 # Enkripsi bcrypt & JWT handler
│   ├── scheduler.py            # APScheduler & Fonnte WhatsApp bot
│   └── main.py                 # FastAPI app entrypoint & endpoints
│
└── frontend/                   # Client-side (HTML5, CSS3, Vanilla JS / SPA)
    ├── index.html              # Halaman publik (edukasi & scanner QR)
    ├── css/
    │   └── style.css           # Styling mobile-first
    └── js/
        ├── api.js              # Fetch API async komunikasi ke backend
        ├── auth.js             # Form register/login & simpan token JWT
        ├── dashboard.js        # Logika toggle sakelar alarm & load jadwal
        └── app.js              # Inisialisasi landing page`,
                  'tree-structure'
                )
              }
              className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs flex items-center gap-1.5 cursor-pointer"
            >
              {copiedKey === 'tree-structure' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKey === 'tree-structure' ? 'Tersalin!' : 'Salin Struktur'}</span>
            </button>
          </div>

          <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto leading-relaxed">
{`sobat-lambung/
├── venv/                       # Virtual environment Python 3.13
├── backend/                    # Server-side (Python / FastAPI)
│   ├── .env                    # Variabel environment (Fonnte token, JWT secret)
│   ├── requirements.txt        # Dependensi Python
│   ├── config.py               # Pengaturan pydantic-settings
│   ├── database.py             # Koneksi SQLAlchemy & engine SQLite
│   ├── models.py               # Model ORM tabel Users
│   ├── schemas.py              # Pydantic validation schemas
│   ├── auth.py                 # Enkripsi bcrypt & JWT handler
│   ├── scheduler.py            # APScheduler & Fonnte WhatsApp bot
│   └── main.py                 # FastAPI app entrypoint & endpoints
│
└── frontend/                   # Client-side (HTML5, CSS3, Vanilla JS / SPA)
    ├── index.html              # Halaman publik (edukasi & scanner QR)
    ├── css/
    │   └── style.css           # Styling mobile-first
    └── js/
        ├── api.js              # Fetch API async komunikasi ke backend
        ├── auth.js             # Form register/login & simpan token JWT
        ├── dashboard.js        # Logika toggle sakelar alarm & load jadwal
        └── app.js              # Inisialisasi landing page`}
          </pre>
        </div>
      )}

      {/* Content 3: Code Viewer */}
      {activeTab === 'code' && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
          {/* File selector bar */}
          <div className="bg-slate-100 p-2 flex overflow-x-auto gap-1 border-b border-slate-200 text-xs no-scrollbar">
            {(
              [
                'models.py',
                'database.py',
                'config.py',
                '.env',
                'requirements.txt',
                'auth.py',
                'scheduler.py',
                'main.py',
              ] as const
            ).map((file) => (
              <button
                key={file}
                onClick={() => setActiveFile(file)}
                className={`px-3 py-1.5 rounded-lg font-mono font-medium whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeFile === file
                    ? 'bg-white text-indigo-700 shadow-xs border border-indigo-200 font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <FileCode className="w-3.5 h-3.5 text-indigo-500" />
                {file}
              </button>
            ))}
          </div>

          {/* Code Header with Copy Button */}
          <div className="bg-slate-900 text-slate-300 px-4 py-2 flex items-center justify-between text-xs font-mono border-b border-slate-800">
            <span>backend/{activeFile}</span>
            <button
              onClick={() => copyToClipboard(fileContents[activeFile], activeFile)}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs flex items-center gap-1 cursor-pointer transition-colors"
            >
              {copiedKey === activeFile ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Tersalin!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Salin Kode</span>
                </>
              )}
            </button>
          </div>

          {/* Code Viewer Body */}
          <pre className="p-4 bg-slate-950 text-slate-100 font-mono text-xs overflow-x-auto leading-relaxed max-h-125">
            {fileContents[activeFile]}
          </pre>
        </div>
      )}
    </section>
  );
};
