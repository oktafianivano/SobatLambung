# Sobat Lambung 🩺

Sobat Lambung adalah aplikasi web edukasi seputar Gastritis dan GERD, dilengkapi dengan fitur pengingat jam makan otomatis melalui WhatsApp untuk membantu penderita menjaga pola makan yang teratur.

## ✨ Fitur Utama

- **Edukasi & Informasi**: Artikel dan panduan seputar kesehatan lambung, Gastritis, dan GERD.
- **Sistem Autentikasi (JWT)**: Registrasi dan Login pengguna yang aman.
- **Dashboard Pengguna**: Manajemen profil dan pengaturan pengingat.
- **Pengingat Makan Otomatis**: Notifikasi WhatsApp yang dikirimkan 3x sehari (06:30, 12:00, 18:30 WIB) menggunakan APScheduler.

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
2. Masuk ke menu **Project Settings > Database** dan salin **Connection string (URI)**.

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

# WhatsApp Notification (Fonnte)
FONNTE_TOKEN=[token_anda_dari_fonnte]
FONNTE_API_URL=https://api.fonnte.com/send

# Security
SECRET_KEY=buat_secret_key_yang_panjang_dan_acak_disini
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Admin Tools
ADMIN_API_KEY=kunci_admin_anda

# CORS (pisahkan dengan koma; sesuaikan IP LAN Anda)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Jalankan server Backend agar bisa diakses dari perangkat lain di jaringan yang sama:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*API sekarang berjalan dan bisa diakses via IP komputer Anda (contoh: `http://192.168.18.28:8000`).*
*Health check tersedia di `GET /health` untuk kebutuhan monitoring/deploy.*

**Versi API**: semua endpoint resmi berada di prefix `/api/v1` (terlihat di Swagger). Prefix lama `/api/...` tetap aktif sebagai alias kompatibilitas, tetapi tidak ditampilkan di dokumentasi.

### 4. Setup Frontend
Buka terminal baru dan masuk ke folder `frontend`:
```bash
cd frontend
```

Instal dependensi Node.js:
```bash
npm install
```

Opsional, buat `frontend/.env` bila backend berada di alamat lain:
```env
VITE_API_URL=http://192.168.18.28:8000
```
Jika dikosongkan, frontend otomatis memakai `http://<host-halaman>:8000`.

Jalankan server pengembangan Frontend agar bisa diakses dari perangkat lain:
```bash
npm run dev -- --host
```
*Aplikasi web sekarang bisa diakses dari HP dengan membuka `http://[IP-KOMPUTER-ANDA]:3000` di browser.*

### 5. Admin Tools (API IT)
Aplikasi ini dilengkapi dengan fitur Admin Tools untuk tim IT agar dapat mengelola data pengguna secara langsung melalui API.

- **Akses**: Tersedia melalui dokumentasi Swagger di `http://[IP-KOMPUTER-ANDA]:8000/docs` pada kategori **Admin Tools**.
- **Kunci Keamanan**: Memerlukan header `x-admin-key` yang nilainya diambil dari variabel `ADMIN_API_KEY` di file `.env` (jangan hardcode di kode).
- **Fitur CRUD**:
  - `POST /api/v1/admin/create`: Menambah user baru secara manual.
  - `GET /api/v1/admin/list`: Melihat daftar semua user.
  - `PUT /api/v1/admin/update/{user_id}`: Mengubah data user.
  - `DELETE /api/v1/admin/delete/{user_id}`: Menghapus user.

### 6. Troubleshooting WhatsApp (Fonnte)
Jika pengingat WhatsApp tidak terkirim atau status di dasbor Fonnte menunjukkan `pending`, lakukan langkah berikut:
1. **Cek Koneksi Perangkat**: Pastikan status perangkat di dasbor Fonnte **Connected**.
2. **Re-scan QR**: Jika koneksi bermasalah, lakukan `Disconnect` lalu *scan* ulang QR code hingga perangkat tertaut kembali dengan benar.
3. **Resend Pesan**: Klik tombol `Resend` pada log pengiriman di dasbor Fonnte untuk memaksa sistem mengirim ulang pesan yang sempat tertunda.
4. **Pastikan HP Aktif**: Pastikan HP yang digunakan untuk *scan* QR terhubung ke internet dan aplikasi WhatsApp tidak dalam mode tidur.

### 7. Menjalankan Test & CI
**Backend (pytest):**
```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

**Frontend (Node test runner via tsx):**
```bash
cd frontend
npm test
```

**Type check + CI:**
```bash
cd frontend
npm run lint
```
Setiap `push`/`pull request` ke branch `main` otomatis menjalankan test backend & frontend melalui GitHub Actions (`.github/workflows/ci.yml`).

### 8. Menjalankan dengan Docker
Prasyarat: **Docker Desktop** dengan Docker Compose v2.

```bash
# 1. Pastikan backend/.env sudah berisi DATABASE_URL, SECRET_KEY, FONNTE_TOKEN, dll.
# 2. Bangun & jalankan seluruh layanan
docker compose up --build -d

# 3. Cek status
docker compose ps
curl http://localhost:8000/health
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000` (docs di `/docs`)
- Ubah alamat API yang ditanam ke frontend saat build:
  ```bash
  # PowerShell
  $env:VITE_API_URL="http://192.168.18.28:8000"; docker compose up --build -d
  ```
- Hentikan: `docker compose down`

```
SobatLambung/
├── .github/workflows/         # CI (GitHub Actions)
├── backend/                   # API FastAPI (Python)
│   ├── app/
│   │   ├── api/               # Endpoint & Dependencies (auth, users, public)
│   │   │   └── router.py      # Registrasi versi API (/api/v1 + alias /api)
│   │   ├── crud/              # Operasi Database (Create, Read, Update)
│   │   ├── auth.py            # Logika Autentikasi (JWT & Hashing)
│   │   ├── config.py          # Konfigurasi Environment
│   │   ├── database.py        # Setup Koneksi Database (Supabase)
│   │   ├── models.py          # Model SQLAlchemy (Tabel Database)
│   │   ├── scheduler.py       # Logika APScheduler (Pengingat WA Fonnte)
│   │   ├── schemas.py         # Pydantic Models (Validasi Data API)
│   │   └── utils.py           # Fungsi Bantuan (Helper/Formatter)
│   ├── tests/                 # Unit test backend (pytest)
│   ├── .env                   # Environment variables rahasia
│   ├── .env.example           # Template konfigurasi environment
│   ├── Dockerfile             # Image backend (uvicorn)
│   ├── main.py                # Entry point FastAPI
│   ├── pytest.ini             # Konfigurasi pytest
│   ├── requirements.txt       # Dependensi Python (produksi)
│   └── requirements-dev.txt   # Dependensi tambahan (development/testing)
│
├── frontend/                  # UI React + Vite (TypeScript)
│   ├── src/
│   │   ├── components/        # UI Components (Modal, Button, dll)
│   │   ├── data/              # Data statis (edukasi, menu)
│   │   ├── logic/             # Logika bisnis & unit test
│   │   ├── services/          # Client HTTP terpusat (api.ts)
│   │   ├── types/             # Definisi tipe TypeScript
│   │   ├── config.ts          # Konfigurasi API URL (VITE_API_URL)
│   │   └── App.tsx            # Entry point React
│   ├── Dockerfile             # Build statis + nginx
│   ├── nginx.conf             # Konfigurasi SPA & cache
│   └── package.json           # Dependensi Node.js
│
├── docker-compose.yml         # Orkestrasi backend + frontend
├── LICENSE                    # Lisensi MIT
└── README.md                  # Dokumentasi
```

## 📝 Lisensi
Proyek ini dilisensikan di bawah **MIT License** — lihat file [LICENSE](LICENSE).
