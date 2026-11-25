# Sobat Lambung 🩺

Sobat Lambung adalah aplikasi web edukasi seputar Gastritis dan GERD, dilengkapi dengan fitur pengingat jam makan otomatis melalui WhatsApp untuk membantu penderita menjaga pola makan yang teratur.

## ✨ Fitur Utama

- **Edukasi & Informasi**: Artikel dan panduan seputar kesehatan lambung, Gastritis, dan GERD.
- **Sistem Autentikasi (JWT)**: Registrasi dan Login pengguna yang aman.
- **Dashboard Pengguna**: Manajemen profil dan pengaturan pengingat.
- **Pengingat Makan Otomatis**: Notifikasi WhatsApp yang dikirimkan 3x sehari (default 07:30, 12:00, 18:30 WIB) menggunakan APScheduler. Jam diatur di satu tempat, yaitu `backend/app/reminder_config.py` (blok `PENGATURAN JAM`) — scheduler dan tampilan frontend ikut menyesuaikan otomatis.

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
ACCESS_TOKEN_EXPIRE_MINUTES=30
# Sliding window: diperpanjang setiap kali sesi di-refresh.
REFRESH_TOKEN_EXPIRE_DAYS=7
# Rate limiting per IP; set false hanya saat load-test lokal
RATE_LIMIT_ENABLED=true

# Cookie autentikasi (lihat bagian Deploy Production untuk mode HTTPS)
COOKIE_SECURE=false
COOKIE_SAMESITE=auto
COOKIE_DOMAIN=

# Admin Tools (WAJIB diganti dengan kunci acak sebelum dipakai publik)
ADMIN_API_KEY=kunci_admin_anda

# Jadwal Pengingat Makan TIDAK lewat .env
# Ubah di: backend/app/reminder_config.py -> blok "PENGATURAN JAM"

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

**Sesi login**: access token berlaku 30 menit. Sesi diperpanjang otomatis lewat refresh token (`POST /api/v1/auth/refresh`) atau endpoint pemulihan `GET /api/v1/auth/session` saat halaman dibuka/di-refresh. Refresh token memakai *sliding window* (default 7 hari): setiap kali diperbarui, masa berlakunya diperpanjang lagi. Pengguna hanya perlu login ulang jika refresh token benar-benar kedaluwarsa, logout, atau mengganti kata sandi.

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
Aplikasi dilindungi berlapis. Di development, CORS menerima origin lokal/LAN secara otomatis; di production, `CORS_ORIGINS` wajib diisi dan hanya origin HTTPS yang diizinkan.

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

**Catatan rate limit di belakang tunnel:** jika memakai ngrok/Cloudflare Tunnel, set `TRUST_PROXY_HEADERS=true` di `.env` supaya batas dihitung per IP pengunjung (bukan IP tunnel yang sama untuk semua orang). Saat diakses langsung lewat LAN, biarkan `false` agar header `X-Forwarded-For` tidak bisa dipalsukan untuk melewati rate limit.

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

### 12. Deploy Production (HTTPS + Cookie Login)

Bagian ini penting agar user **tidak ter-logout saat refresh browser** dan cookie tampil dengan centang **Secure** di DevTools.

#### Penyebab umum token/cookie hilang saat refresh

| Penyebab | Akibat |
| --- | --- |
| `APP_ENV` bukan `production` | Cookie tidak memakai flag `Secure`. |
| Backend diakses lewat HTTP, bukan HTTPS | Browser membuang cookie `Secure`. |
| Frontend & backend beda domain (mis. Vercel + Render) | Cookie dianggap third-party, diblokir browser. |
| `COOKIE_SAMESITE=lax` pada beda site | Cookie tidak dikirim pada fetch lintas site. |
| `COOKIE_DOMAIN` salah (URL/port/subdomain lain) | Browser menolak `Set-Cookie`. |
| CSRF token hanya dibaca dari cookie | JavaScript beda origin tidak bisa membaca cookie API. |

Backend sudah menangani dua skenario:

1. **Same-origin / same-site (disarankan).** Frontend dan API berada di domain yang sama (atau subdomain dari parent domain yang sama). Nginx pada image frontend sudah mem-proxy `/api/` ke service `backend`, jadi `VITE_API_URL` cukup dikosongkan.
2. **Beda origin.** `COOKIE_SAMESITE=auto` otomatis memakai `SameSite=None; Secure; Partitioned`, dan token CSRF juga dikirim di body response login/refresh agar tetap bisa dipakai JavaScript.

> Rekomendasi terkuat: gunakan **satu domain** untuk frontend dan API. Safari dan sebagian browser tetap membatasi cookie third-party meskipun `SameSite=None`; same-origin menghilangkan masalah itu sepenuhnya.

> **Catatan HTTP:** browser tidak mengizinkan cookie `Secure` di koneksi HTTP. Jika production masih diakses lewat HTTP, backend otomatis mengirim cookie tanpa `Secure` + mencatat warning di log agar login tidak langsung hilang saat refresh. Ini hanya jaring pengaman; production tetap **wajib HTTPS** agar flag `Secure` aktif.

#### Opsi A — Same-origin (disarankan, Docker Compose)

Root `.env` (dibaca `docker-compose.yml`):
```env
APP_ENV=production
COOKIE_SECURE=true
COOKIE_SAMESITE=auto
COOKIE_DOMAIN=
TRUST_PROXY_HEADERS=true
VITE_API_URL=
```

`backend/.env`:
```env
APP_ENV=production
SECRET_KEY=<acak-minimal-32-karakter>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
COOKIE_SECURE=true
COOKIE_SAMESITE=auto
COOKIE_DOMAIN=
DATABASE_URL=postgresql://...
FONNTE_TOKEN=...
ADMIN_API_KEY=<kunci-acak>
# WAJIB origin halaman yang dipakai browser (HTTPS)
CORS_ORIGINS=https://sobatlambung.id
```

Jalankan:
```bash
docker compose up -d --build
```
Akses lewat **HTTPS** (mis. Cloudflare Tunnel / reverse proxy Caddy/Nginx yang menterminasi TLS). Pastikan proxy mengirim `X-Forwarded-Proto: https`; `TRUST_PROXY_HEADERS=true` membuat HSTS dan rate limit bekerja benar.

#### Opsi B — Frontend & backend beda domain

Root `.env`:
```env
APP_ENV=production
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
TRUST_PROXY_HEADERS=true
VITE_API_URL=https://api.sobatlambung.id
```

`backend/.env`:
```env
APP_ENV=production
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=
CORS_ORIGINS=https://sobatlambung.id
```

Catatan:
- `COOKIE_DOMAIN` **jangan** diisi bila kedua host tidak berbagi parent domain.
- Harus HTTPS di kedua sisi; `SameSite=None` tanpa `Secure` akan ditolak browser.
- Token CSRF tetap bekerja karena frontend menyimpan `csrf_token` dari body response **hanya di memori** dan mengirimnya sebagai header `X-CSRF-Token`. Token ini tidak pernah ditulis ke `localStorage`/`sessionStorage`.
- `access_token` dan `refresh_token` selalu `HttpOnly`; JavaScript tidak pernah membaca atau menyimpannya.

#### Opsi C — Subdomain dari domain yang sama

Contoh: frontend `https://sobatlambung.id`, API `https://api.sobatlambung.id`.

```env
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.sobatlambung.id
CORS_ORIGINS=https://sobatlambung.id
VITE_API_URL=https://api.sobatlambung.id
```

`COOKIE_DOMAIN` harus berupa hostname parent tanpa `https://` dan tanpa port.

#### Opsi D — Railway: dua service, satu origin lewat proxy nginx

Domain `*.up.railway.app` adalah **public suffix** (terdaftar di Public Suffix List). Artinya `frontend.up.railway.app` dan `backend.up.railway.app` dianggap **site berbeda** oleh browser, sehingga cookie `SameSite=Lax` tidak akan dikirim dan user ter-logout saat refresh.

Solusi paling andal: biarkan browser hanya melihat **satu origin** (domain frontend), lalu nginx frontend mem-proxy `/api` ke backend.

**Frontend service → Variables:**
```env
# Kosongkan agar bundle memakai origin yang sama (bukan URL backend langsung)
VITE_API_URL=
# Private networking (disarankan). Ganti nama service sesuai Railway.
BACKEND_URL=http://sobatlambung-production.railway.internal:8000
# Resolver internal Railway
NGINX_RESOLVER=[fd12::10] ipv6=on
```

Jika private networking tidak tersedia, boleh memakai URL publik backend:
```env
BACKEND_URL=https://sobatlambung-production.up.railway.app
NGINX_RESOLVER=[fd12::10] ipv6=on
```

**Backend service → Variables:**
```env
APP_ENV=production
COOKIE_SECURE=true
COOKIE_SAMESITE=auto
COOKIE_DOMAIN=
TRUST_PROXY_HEADERS=true
CORS_ORIGINS=https://sparkling-unity-production.up.railway.app
```

Lalu **redeploy frontend** (agar `VITE_API_URL` kosong ikut ter-build) dan backend.

Verifikasi dari terminal:
```bash
curl -i -X POST https://sparkling-unity-production.up.railway.app/api/v1/auth/logout \
  -H 'Origin: https://sparkling-unity-production.up.railway.app'
```
Response harus berisi `Set-Cookie: ...; Secure; SameSite=lax` (same-origin), bukan `SameSite=lax` tanpa `Secure`.

> Jangan set `COOKIE_DOMAIN=.up.railway.app`. Itu public suffix; browser akan menolak cookie. Biarkan `COOKIE_DOMAIN` kosong.

> Jika tetap memilih dua origin terpisah, `SameSite=None; Secure; Partitioned` bisa bekerja di Chrome, tetapi Safari/WebView tetap dapat memblokir cookie third-party. Same-origin adalah satu-satunya solusi yang konsisten.

#### Checklist setelah deploy

1. `GET https://<backend>/health` harus menampilkan `"environment": "production"`. Jika masih `development`, cookie tidak akan memakai `Secure` dan `SameSite=None` diturunkan menjadi `Lax` (penyebab logout saat refresh).
2. `GET https://<backend>/docs` harus **404** di production.
3. Buka DevTools → **Application → Cookies**.
4. Pastikan `access_token`, `refresh_token`, dan `csrf_token` memiliki:
   - **Secure** ✓
   - **HttpOnly** ✓ untuk `access_token` & `refresh_token`
   - **SameSite** sesuai skenario (`Lax` untuk same-site, `None` untuk beda site)
   - **Expires/Max-Age** terisi (bukan *Session*)
5. Refresh halaman (F5) → user tetap login.
6. Tunggu access token kedaluwarsa (atau hapus cookie `access_token` saja) → refresh halaman harus tetap login karena `GET /api/v1/auth/session` memperbarui sesi dari `refresh_token`.
7. Jika masih logout: cek `CORS_ORIGINS` sama persis dengan origin di address bar (termasuk `https://` dan tanpa trailing slash). Hapus cookie lama di kedua domain sebelum menguji ulang.

## 📝 Lisensi
Proyek ini dilisensikan di bawah **MIT License** — lihat file [LICENSE](LICENSE).
