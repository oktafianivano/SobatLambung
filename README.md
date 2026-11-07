# Sobat Lambung 🩺

Sobat Lambung adalah aplikasi web edukasi seputar Gastritis dan GERD, dilengkapi dengan fitur pengingat jam makan otomatis melalui WhatsApp untuk membantu penderita menjaga pola makan yang teratur.

## ✨ Fitur Utama

- **Edukasi & Informasi**: Artikel dan panduan seputar kesehatan lambung, Gastritis, dan GERD.
- **Sistem Autentikasi (JWT)**: Registrasi dan Login pengguna yang aman.
- **Dashboard Pengguna**: Manajemen profil dan pengaturan pengingat.
- **Pengingat Makan Otomatis**: Notifikasi WhatsApp yang dikirimkan 3x sehari (07:00, 12:00, 18:30 WIB) menggunakan APScheduler.

## 🛠️ Teknologi yang Digunakan

**Frontend:**
- [React](https://reactjs.org/) + [Vite](https://vitejs.dev/)
- [TypeScript](https://www.typescriptlang.org/)

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) (Python)
- [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
- [APScheduler](https://apscheduler.readthedocs.io/) (Background Tasks)
- JWT (JSON Web Tokens) & Passlib (Autentikasi & Hashing)

**Database:**
- [Supabase](https://supabase.com/) (PostgreSQL)

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

Pastikan kamu sudah menginstal **Node.js**, **Python (3.9+)**, dan memiliki akun **Supabase**.

### 1. Kloning Repositori
```bash
git clone https://github.com/username/sobat-lambung.git
cd sobat-lambung
```

### 2. Setup Database (Supabase)
1. Buat proyek baru di [Supabase](https://supabase.com/).
2. Masuk ke menu **Project Settings > Database** dan salin **Connection string (URI)**. Pastikan menggunakan format PostgreSQL (contoh: `postgresql://postgres.[namaproject]:[password]@aws-0-region.pooler.supabase.com:6543/postgres`).

### 3. Setup Backend
Buka terminal baru dan masuk ke folder `backend`:
```bash
cd backend
```

Buat dan aktifkan *Virtual Environment*:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Instal dependensi:
```bash
pip install -r requirements.txt
```

Buat file `.env` di dalam folder `backend` dan isi dengan konfigurasi berikut:
```env
# Database Configuration (Supabase)
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[db_name]

# Security
SECRET_KEY=buat_secret_key_yang_panjang_dan_acak_disini
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Jalankan server Backend:
```bash
uvicorn main:app --reload --port 8000
```
*API sekarang berjalan di `http://localhost:8000` dan dokumentasi Swagger di `http://localhost:8000/docs`.*

### 4. Setup Frontend
Buka terminal baru dan masuk ke folder `frontend`:
```bash
cd frontend
```

Instal dependensi Node.js:
```bash
npm install
```

Jalankan server pengembangan Frontend:
```bash
npm run dev
```
*Aplikasi web sekarang berjalan di `http://localhost:3000` (atau port yang tertera di terminal).*

---

## 📂 Struktur Direktori Utama
```
SobatLambung/
├── backend/                # API FastAPI (Python)
│   ├── app/
│   │   ├── api/            # Endpoint & Dependencies (auth, users, public)
│   │   ├── crud/           # Operasi Database (Create, Read, Update)
│   │   ├── auth.py         # Logika Autentikasi (JWT & Hashing)
│   │   ├── config.py       # Konfigurasi Environment
│   │   ├── database.py     # Setup Koneksi Database (Supabase)
│   │   ├── models.py       # Model SQLAlchemy (Tabel Database)
│   │   ├── scheduler.py    # Logika APScheduler (Pengingat WA Fonnte)
│   │   ├── schemas.py      # Pydantic Models (Validasi Data API)
│   │   └── utils.py        # Fungsi Bantuan (Helper/Formatter)
│   ├── scripts/            # Script tambahan (Opsional)
│   ├── .env                # Environment variables rahasia
│   ├── main.py             # Entry point FastAPI
│   └── requirements.txt    # Dependensi Python
│
└── frontend/               # UI React + Vite (TypeScript)
    ├── src/
    │   ├── components/     # UI Components (Modal, Button, dll)
    │   ├── pages/          # Halaman (Dashboard, dll)
    │   └── App.tsx         # Entry point React
    └── package.json        # Dependensi Node.js
```

## 📝 Lisensi
Proyek ini dibuat untuk keperluan edukasi dan open-source.