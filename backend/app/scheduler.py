import logging
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sobat_lambung_scheduler")

MEAL_TEMPLATES = {
    "breakfast": {
        "title": "🌅 Waktunya Sarapan Sehat (07:00 WIB)",
        "menu": ["Bubur ayam tanpa sambal / kuah kuning ringan", "Oatmeal dengan pisang matang & madu", "Roti gandum panggang + telur rebus"],
        "advice": "Jangan biarkan lambung kosong lebih dari 12 jam sejak malam. Asam lambung pagi hari dapat mengikis mukosa jika tidak dinetralisir sarapan rendah asam."
    },
    "lunch": {
        "title": "☀️ Waktunya Makan Siang (12:00 WIB)",
        "menu": ["Nasi putih pulen hangat + sup wortel bayam + ayam suwir kukus", "Ikan nila/salmon kukus bumbu kunyit + tahu kukus", "Kentang tumbuk (mashed potato) + telur dadar minim minyak"],
        "advice": "Kunyah makanan perlahan (minimal 20-30 kali). Hindari kopi dingin, minuman bersoda, dan gorengan pedas di kantin kampus saat istirahat kuliah."
    },
    "dinner": {
        "title": "🌙 Waktunya Makan Malam (18:30 WIB)",
        "menu": ["Sup labu siam / wortel hangat + tempe bacem panggang", "Nasi tim ayam jamur rendah lemak", "Bubur kacang hijau kuah santan sangat encer/tanpa santan"],
        "advice": "Beri jeda minimal 2-3 jam antara makan malam dan waktu tidur agar asam lambung tidak naik kembali ke esofagus (mencegah reflux/GERD)."
    }
}


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
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(send_fonnte_message(user.no_wa, msg))
                else:
                    asyncio.run(send_fonnte_message(user.no_wa, msg))
            except Exception as e:
                logger.error(f"Error mengirim ke user {user.id}: {e}")
    finally:
        db.close()


def init_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(
        trigger_scheduled_broadcast,
        CronTrigger(hour=7, minute=0),
        args=["breakfast"],
        id="alarm_breakfast",
        name="Pengingat Sarapan Sobat Lambung",
        replace_existing=True
    )

    scheduler.add_job(
        trigger_scheduled_broadcast,
        CronTrigger(hour=12, minute=0),
        args=["lunch"],
        id="alarm_lunch",
        name="Pengingat Makan Siang Sobat Lambung",
        replace_existing=True
    )

    scheduler.add_job(
        trigger_scheduled_broadcast,
        CronTrigger(hour=18, minute=30),
        args=["dinner"],
        id="alarm_dinner",
        name="Pengingat Makan Malam Sobat Lambung",
        replace_existing=True
    )

    return scheduler
