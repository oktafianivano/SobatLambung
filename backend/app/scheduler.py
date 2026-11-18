import logging
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.config import settings
from app.reminder_config import MEAL_ORDER, reminder_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sobat_lambung_scheduler")

# Dibangun sekali saat import. Environment sudah final di titik ini, jadi judul
# pesan selalu mengikuti MEAL_*_TIME dari .env / Railway Variables dan tidak
# bisa lagi tertinggal dari jam yang benar-benar dipakai CronTrigger.
MEAL_TEMPLATES = reminder_config.build_templates()


def build_reset_otp_message(user_name: str, otp_code: str, expire_minutes: int) -> str:
    return (
        f"Halo *{user_name}*! 👋\n"
        f"Permintaan reset kata sandi akun *Sobat Lambung* 🥣\n\n"
        f"Kode OTP Anda:\n"
        f"*{otp_code}*\n\n"
        f"Kode ini berlaku selama *{expire_minutes} menit* dan hanya dapat digunakan satu kali.\n"
        f"Jangan bagikan kode ini kepada siapa pun, termasuk pihak yang mengaku sebagai admin Sobat Lambung.\n\n"
        f"_Jika Anda tidak merasa meminta reset kata sandi, abaikan pesan ini. Kata sandi Anda tidak akan berubah._"
    )


def build_verification_otp_message(user_name: str, otp_code: str, expire_minutes: int) -> str:
    return (
        f"Halo *{user_name}*! 👋\n"
        f"Verifikasi nomor WhatsApp akun *Sobat Lambung* 🥣\n\n"
        f"Kode OTP Anda:\n"
        f"*{otp_code}*\n\n"
        f"Kode ini berlaku selama *{expire_minutes} menit* dan hanya dapat digunakan satu kali.\n"
        f"Jangan bagikan kode ini kepada siapa pun, termasuk pihak yang mengaku sebagai admin Sobat Lambung.\n\n"
        f"_Jika Anda tidak merasa mendaftar di Sobat Lambung, abaikan pesan ini._"
    )


def build_whatsapp_message(user_name: str, meal_key: str) -> str:
    tpl = MEAL_TEMPLATES.get(meal_key, MEAL_TEMPLATES["lunch"])
    menus = "\n".join([f"  • {m}" for m in tpl["menu"]])
    
    return (
        f"Halo *{user_name}*! 👋\n"
        f"Pengingat dari *Sobat Lambung* 🥣\n\n"
        f"*{tpl['title']}*\n\n"
        f"🍽️ *Rekomendasi Menu Mahasiswa Aman Lambung:*\n"
        f"{menus}\n\n"
        f"💡 *Catatan Medis Sobat Lambung:*\n"
        f"{tpl['advice']}\n\n"
        f"_Tetap teratur makan di tengah padatnya tugas & kuliah ya!_ 😊"
    )


async def send_fonnte_message(target_wa: str, message: str) -> dict:
    if not settings.FONNTE_TOKEN or settings.FONNTE_TOKEN == "YOUR_FONNTE_TOKEN_HERE":
        logger.warning(f"[SIMULASI FONNTE] Token belum diisi. Pesan ke {target_wa}:\n{message}")
        return {"status": False, "reason": "TOKEN_PLACEHOLDER", "simulated": True}

    clean_target = target_wa.strip()
    if clean_target.startswith("0"):
        clean_target = "62" + clean_target[1:]
    elif not clean_target.startswith("62"):
        clean_target = "62" + clean_target

    headers = {"Authorization": settings.FONNTE_TOKEN}
    payload = {
        "target": clean_target,
        "message": message
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.FONNTE_API_URL, headers=headers, data=payload)
            data = response.json()
            logger.info(f"Fonnte Response untuk {clean_target}: {data}")
            return data
    except Exception as exc:
        logger.error(f"Gagal kirim pesan WhatsApp ke {clean_target}: {exc}")
        return {"status": False, "error": str(exc)}


def trigger_scheduled_broadcast(meal_key: str):
    db: Session = SessionLocal()
    try:
        active_users = db.query(User).filter(User.is_alarm_active == True).all()
        logger.info(f"Memulai broadcast pengingat {meal_key} ke {len(active_users)} pengguna aktif.")
        
        import asyncio
        for user in active_users:
            msg = build_whatsapp_message(user.nama, meal_key)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_fonnte_message(user.no_wa, msg))
                loop.close()
            except Exception as e:
                logger.error(f"Error mengirim ke user {user.id}: {e}")
    finally:
        db.close()

# Zona waktu acuan pengingat. Wajib dipakai eksplisit di setiap CronTrigger:
# CronTrigger tanpa `timezone` memakai zona waktu lokal server (Railway = UTC),
# sehingga jadwal 07:30 akan terkirim 14:30 WIB.
JOB_NAMES = {
    "breakfast": "Pengingat Sarapan Sobat Lambung",
    "lunch": "Pengingat Makan Siang Sobat Lambung",
    "dinner": "Pengingat Makan Malam Sobat Lambung",
}


def init_scheduler():
    scheduler = BackgroundScheduler(timezone=reminder_config.MEAL_TIMEZONE)

    for meal_key in MEAL_ORDER:
        hour, minute = reminder_config.hour_minute(meal_key)
        scheduler.add_job(
            trigger_scheduled_broadcast,
            CronTrigger(
                hour=hour,
                minute=minute,
                timezone=reminder_config.MEAL_TIMEZONE,
            ),
            args=[meal_key],
            id=f"alarm_{meal_key}",
            name=JOB_NAMES[meal_key],
            replace_existing=True,
        )

    return scheduler
