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
```

Jalankan server Backend agar bisa diakses dari perangkat lain di jaringan yang sama:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*API sekarang berjalan dan bisa diakses via IP komputer Anda (contoh: `http://192.168.18.28:8000`).*

### 4. Setup Frontend
Buka terminal baru dan masuk ke folder `frontend`:
```bash
cd frontend
```

Instal dependensi Node.js:
```bash
npm install
```

Jalankan server pengembangan Frontend agar bisa diakses dari perangkat lain:
```bash
npm run dev -- --host
```
*Aplikasi web sekarang bisa diakses dari HP dengan membuka `http://[IP-KOMPUTER-ANDA]:5173` di browser.*

### 5. Admin Tools (API IT)
Aplikasi ini dilengkapi dengan fitur Admin Tools untuk tim IT agar dapat mengelola data pengguna secara langsung melalui API.

- **Akses**: Tersedia melalui dokumentasi Swagger di `http://[IP-KOMPUTER-ANDA]:8000/docs` pada kategori **Admin Tools**.
- **Kunci Keamanan**: Memerlukan `x-admin-key` dengan nilai `sobatlambung_it_2026` di setiap permintaan.
- **Fitur CRUD**:
  - `POST /api/admin/create`: Menambah user baru secara manual.
  - `GET /api/admin/list`: Melihat daftar semua user.
  - `PUT /api/admin/update/{user_id}`: Mengubah data user.
  - `DELETE /api/admin/delete/{user_id}`: Menghapus user.

### 6. Troubleshooting WhatsApp (Fonnte)
Jika pengingat WhatsApp tidak terkirim atau status di dasbor Fonnte menunjukkan `pending`, lakukan langkah berikut:
1. **Cek Koneksi Perangkat**: Pastikan status perangkat di dasbor Fonnte **Connected**.
2. **Re-scan QR**: Jika koneksi bermasalah, lakukan `Disconnect` lalu *scan* ulang QR code hingga perangkat tertaut kembali dengan benar.
3. **Resend Pesan**: Klik tombol `Resend` pada log pengiriman di dasbor Fonnte untuk memaksa sistem mengirim ulang pesan yang sempat tertunda.
4. **Pastikan HP Aktif**: Pastikan HP yang digunakan untuk *scan* QR terhubung ke internet dan aplikasi WhatsApp tidak dalam mode tidur.

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
