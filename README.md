# Sobat Lambung 🩺

Sobat Lambung adalah aplikasi web edukasi seputar Gastritis dan GERD, dilengkapi dengan fitur pengingat jam makan otomatis melalui WhatsApp untuk membantu penderita menjaga pola makan yang teratur.

## ✨ Fitur Utama

- **Edukasi & Informasi**: Artikel dan panduan seputar kesehatan lambung, Gastritis, dan GERD.
- **Sistem Autentikasi (JWT)**: Registrasi dan Login pengguna yang aman.
- **Dashboard Pengguna**: Manajemen profil dan pengaturan pengingat.
- **Pengingat Makan Otomatis**: Notifikasi WhatsApp yang dikirimkan 3x sehari (07:30, 12:00, 18:30 WIB) menggunakan APScheduler.

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
# SECRET_KEY minimal 32 karakter acak:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=buat_secret_key_yang_panjang_dan_acak_disini
ALGORITHM=HS256
# 720 menit = 12 jam (cukup untuk sehari pameran)
ACCESS_TOKEN_EXPIRE_MINUTES=720
# Rate limiting per IP; set false hanya saat load-test lokal
RATE_LIMIT_ENABLED=true

# Admin Tools (WAJIB diganti dengan kunci acak sebelum dipakai publik)
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
- **Kunci Keamanan**: Memerlukan header `x-admin-key` yang nilainya diambil dari variabel `ADMIN_API_KEY` di file `.env` (jangan hardcode di kode). Kunci dibandingkan secara *constant-time* agar tidak bisa ditebak lewat analisis waktu.
- **Fitur CRUD**:
  - `POST /api/v1/admin/create`: Menambah user baru secara manual. **Wajib** mengirim `nama`, `no_wa`, dan `password` (minimal 6 karakter).
  - `GET /api/v1/admin/list`: Melihat daftar semua user. Nomor WhatsApp ditampilkan tersamarkan (`no_wa_masked`).
  - `PUT /api/v1/admin/update/{user_id}`: Mengubah data user (`nama`, `no_wa`, `password`, `is_alarm_active` — semua opsional).
  - `DELETE /api/v1/admin/delete/{user_id}`: Menghapus user.
  - `GET /api/v1/admin/audit-logs?limit=50`: Melihat riwayat aktivitas admin (create/update/delete) beserta waktu dan alamat IP.

Contoh payload create:
```json
{
  "nama": "Budi Santoso",
  "no_wa": "081234567891",
  "password": "rahasia123",
  "is_alarm_active": true
}
```

Setiap create/update/delete otomatis tercatat di tabel `audit_logs` (aktor, aksi, ID target, ringkasan perubahan, IP, waktu). Password tidak pernah ikut dicatat.

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

### 8. Migrasi Database (Alembic)
Skema database dikelola dengan **Alembic**. Migrasi awal bersifat *baseline*: menandai skema yang sudah ada tanpa mengubah/menghapus data.

```bash
cd backend

# Terapkan semua migrasi (wajib sebelum deploy / setelah pull)
alembic upgrade head

# Cek apakah model sudah sama dengan database
alembic check

# Setelah mengubah app/models.py, buat migrasi baru
alembic revision --autogenerate -m "tambah kolom x"

# Lihat riwayat & status
alembic history
alembic current

# Rollback satu langkah
alembic downgrade -1
```

Catatan:
- URL database diambil dari `backend/.env` (`DATABASE_URL`), **bukan** dari `alembic.ini`, jadi tidak ada kredensial di repo.
- Di mode `APP_ENV=development` aplikasi masih menjalankan `create_all` agar praktis saat ngoding. Di `APP_ENV=production` pembuatan tabel dilewati — jalankan `alembic upgrade head` (sudah otomatis di Dockerfile).
- Selalu review file migrasi hasil `--autogenerate` sebelum commit.

### 9. Cara Mengubah Jadwal Pengingat
Jika ingin mengganti jadwal pengingat (misal: sarapan jadi jam 06:30), Anda perlu mengubahnya di beberapa tempat agar konsisten. Berikut langkah-langkahnya:

1. **Backend (Logika Cron Job)**
   Buka `backend/app/scheduler.py`, cari `CronTrigger` untuk `breakfast`, `lunch`, atau `dinner`. Ubah `hour` dan `minute`-nya:
   ```python
   # Contoh: ubah sarapan ke 06:30
   scheduler.add_job(..., CronTrigger(hour=6, minute=30), args=["breakfast"], ...)
   ```

2. **Backend (Endpoint API)**
   Buka `backend/app/api/endpoints/public.py` dan perbarui jam di `get_static_schedules` agar frontend menerima data yang akurat:
   ```python
   {"id": "breakfast", "time": "06:30 WIB", ...}
   ```

3. **Frontend (Logika Bisnis)**
   Buka `frontend/src/logic/sobatLambung.ts`. Ubah `hour` dan `minute` pada `STATIC_SCHEDULES`:
   ```typescript
   { id: 'breakfast', time: '06:30 WIB', hour: 6, minute: 30, ... }
   ```

4. **Frontend (Test)**
   Buka `frontend/src/logic/sobatLambung.test.ts` dan sesuaikan ekspektasi waktu pada unit test agar tes tetap *pass*.

5. **Frontend (UI Mockup)**
   Jika perlu, perbarui juga `frontend/src/components/WhatsAppPhoneMockup.tsx` pada bagian `time: '06:30'`.

*Catatan: Setelah mengubah file-file di atas, jangan lupa restart backend (uvicorn) dan pastikan UI frontend juga mencerminkan perubahan tersebut.*

### 10. Tampilan di HP (Responsif)
UI memakai **Tailwind CSS** dengan pendekatan *mobile-first*, jadi satu kode yang sama dipakai di semua ukuran layar (tidak ada layout terpisah untuk HP). Titik henti (*breakpoint*) yang dipakai:

| Prefix | Lebar layar | Perilaku |
| --- | --- | --- |
| *(tanpa prefix)* | 0 – 639px | Layout HP: menu tab bisa digeser, tombol penuh, kartu menumpuk |
| `sm:` | ≥ 640px | Tablet kecil: dua kolom, teks lebih besar |
| `md:` | ≥ 768px | Menu navigasi desktop muncul, grid 3 kolom |
| `lg:` | ≥ 1024px | Grid 12 kolom (halaman Bagikan) & padding lebar |

Beberapa hal yang sudah dijaga agar aman di HP:

- **Tidak ada scroll horizontal.** `body` memakai `overflow-x: clip` dan setiap baris memakai `flex-wrap` atau `min-w-0`.
- **Modal login/daftar bisa di-scroll.** Saat keyboard HP muncul, tombol "Masuk" tetap bisa dijangkau (`overflow-y-auto` + `min-h-full`).
- **Strip menu HP otomatis menggeser** ke tab yang sedang aktif (`Navbar.tsx`, `useEffect` + `scrollTo`).
- **Tinggi halaman memakai `min-h-dvh`** agar tidak terpotong oleh address bar browser HP.
- **Kartu dasbor alarm memakai `w-full md:min-w-70`**, jadi tidak melebar keluar layar di HP 320px.

Cara cepat memeriksa: buka aplikasi di Chrome → tekan `F12` → klik ikon **Toggle device toolbar** (`Ctrl + Shift + M`) → pilih **iPhone SE (375px)** atau **Galaxy S8 (360px)**. Kalau tidak ada scroll ke samping dan semua tombol bisa diklik, tampilan sudah aman.

### 11. Lapisan Keamanan (Security Hardening)
Aplikasi dilindungi berlapis tanpa membatasi CORS, sehingga tetap nyaman dipakai saat pameran di jaringan lokal yang IP-nya berubah-ubah.

| # | Lapisan | Fungsi |
| --- | --- | --- |
| 1 | **Rate limiting (`slowapi`)** | Batasi percobaan per IP: login 10/menit, register 5/menit, minta OTP 5/menit, reset OTP 10/menit, test notifikasi 5/menit, profil 20/menit, admin 60/menit. Respons `429` berisi `detail` + header `Retry-After`. |
| 2 | **Security headers** | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, dan `Content-Security-Policy`. CSP API sangat ketat (`default-src 'none'`); `/docs` dan `/redoc` diberi pengecualian karena Swagger memuat aset CDN. |
| 3 | **Masking data** | `UserResponse` tidak pernah memuat `password_hash`; nomor WhatsApp disediakan dalam bentuk `no_wa_masked` (contoh `6281*****7890`). |
| 4 | **Sanitasi input** | Nama hanya boleh huruf/angka/spasi/titik/koma/apostrof/tanda hubung; karakter `< > { } $ \`` dan kontrol ditolak. Nomor WA hanya boleh angka dan `+ - ( ) .`. OTP wajib tepat 6 angka. |
| 5 | **Hardening JWT** | Token memuat `iat`, `nbf`, `exp`, `jti`, dan `typ=access`. Masa berlaku default **12 jam**, toleransi jam 10 detik, token bertipe lain ditolak. Ganti password membuat token lama otomatis tidak berlaku (`pwd` fingerprint). |
| 6 | **Keamanan OTP WhatsApp** | OTP 6 digit acak, disimpan sebagai hash bcrypt, berlaku 10 menit, maksimal 5 percobaan, jeda kirim ulang 60 detik, dan respons permintaan selalu generik (tidak membocorkan apakah nomor terdaftar). |
| 7 | **Audit log admin** | Setiap create/update/delete admin dicatat ke tabel `audit_logs` (aktor, aksi, target, ringkasan, IP, waktu). Bisa dibaca via `GET /api/v1/admin/audit-logs`. |
| 8 | **Row Level Security (Supabase)** | RLS diaktifkan pada `users`, `password_reset_otps`, dan `audit_logs`. Role `anon`/`authenticated` Supabase tidak bisa membaca data langsung lewat REST API. Aplikasi tetap berjalan karena terkoneksi sebagai owner database. |

**Catatan HSTS & HTTPS:** header `Strict-Transport-Security` hanya dikirim jika request sudah HTTPS (atau di belakang proxy/tunnel yang mengirim `X-Forwarded-Proto: https`). Saat demo LAN masih `http`, header ini otomatis tidak dikirim karena browser akan mengabaikannya. Jika ingin HTTPS asli tanpa peringatan browser, jalankan aplikasi di belakang tunnel seperti Cloudflare Tunnel atau ngrok, lalu akses URL `https://...` yang diberikan.

**Menjalankan migrasi keamanan:**
```bash
cd backend
alembic upgrade head   # membuat audit_logs + mengaktifkan RLS
alembic check          # memastikan tidak ada perubahan skema yang tertinggal
```

**Menjalankan test keamanan:**
```bash
cd backend
pytest tests/test_security.py -q
```
Test mencakup sanitasi anti-XSS, masking, JWT kedaluwarsa/dipalsukan, guard bcrypt, security headers, rate limit 429, audit CRUD admin, dan pengecekan RLS pada file migrasi.

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
│   ├── alembic/               # Migrasi database (env.py + versions/)
│   ├── tests/                 # Unit test backend (pytest)
│   ├── .env                   # Environment variables rahasia
│   ├── .env.example           # Template konfigurasi environment
│   ├── alembic.ini            # Konfigurasi Alembic (tanpa kredensial)
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
