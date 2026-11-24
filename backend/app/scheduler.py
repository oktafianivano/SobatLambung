
import asyncio
import logging
import re

import httpx

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.config import settings
from app.reminder_config import MEAL_ORDER, reminder_config


logger = logging.getLogger("sobat_lambung_scheduler")

MEAL_TEMPLATES = reminder_config.build_templates()


JOB_NAMES = {
    "breakfast": "Pengingat Sarapan Sobat Lambung",
    "lunch": "Pengingat Makan Siang Sobat Lambung",
    "dinner": "Pengingat Makan Malam Sobat Lambung",
}


HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


# OTP message builders
def build_reset_otp_message(
    user_name: str,
    otp_code: str,
    expire_minutes: int,
) -> str:
    return (
        f"Halo *{user_name}*! 👋\n"
        f"Permintaan reset kata sandi akun *Sobat Lambung* 🥣\n\n"
        f"Kode OTP Anda:\n"
        f"*{otp_code}*\n\n"
        f"Kode ini berlaku selama *{expire_minutes} menit* "
        f"dan hanya dapat digunakan satu kali.\n"
        f"Jangan bagikan kode ini kepada siapa pun, "
        f"termasuk pihak yang mengaku sebagai admin Sobat Lambung.\n\n"
        f"_Jika Anda tidak merasa meminta reset kata sandi, "
        f"abaikan pesan ini. Kata sandi Anda tidak akan berubah._"
    )


def build_verification_otp_message(
    user_name: str,
    otp_code: str,
    expire_minutes: int,
) -> str:
    return (
        f"Halo *{user_name}*! 👋\n"
        f"Verifikasi nomor WhatsApp akun *Sobat Lambung* 🥣\n\n"
        f"Kode OTP Anda:\n"
        f"*{otp_code}*\n\n"
        f"Kode ini berlaku selama *{expire_minutes} menit* "
        f"dan hanya dapat digunakan satu kali.\n"
        f"Jangan bagikan kode ini kepada siapa pun, "
        f"termasuk pihak yang mengaku sebagai admin Sobat Lambung.\n\n"
        f"_Jika Anda tidak merasa mendaftar di Sobat Lambung, "
        f"abaikan pesan ini._"
    )


# WhatsApp message builder
def build_whatsapp_message(
    user_name: str,
    meal_key: str,
) -> str:
    template = MEAL_TEMPLATES.get(
        meal_key,
        MEAL_TEMPLATES["lunch"],
    )

    menus = "\n".join(
        f"  • {menu}"
        for menu in template["menu"]
    )

    return (
        f"Halo *{user_name}*! 👋\n"
        f"Pengingat dari *Sobat Lambung* 🥣\n\n"
        f"*{template['title']}*\n\n"
        f"🍽️ *Rekomendasi Menu Mahasiswa Aman Lambung:*\n"
        f"{menus}\n\n"
        f"💡 *Catatan Medis Sobat Lambung:*\n"
        f"{template['advice']}\n\n"
        f"_Tetap teratur makan di tengah padatnya tugas "
        f"& kuliah ya!_ 😊"
    )


# WhatsApp number normalization
def normalize_whatsapp_number(target_wa: str) -> str:
    if not target_wa:
        raise ValueError("WhatsApp number is empty")

    clean_target = re.sub(
        r"[\s\-()+]",
        "",
        target_wa.strip(),
    )

    if not clean_target.isdigit():
        raise ValueError("Invalid WhatsApp number")

    if clean_target.startswith("0"):
        clean_target = "62" + clean_target[1:]
    elif clean_target.startswith("8"):
        clean_target = "62" + clean_target
    elif not clean_target.startswith("62"):
        raise ValueError("Unsupported WhatsApp country code")

    if not 8 <= len(clean_target) <= 15:
        raise ValueError("Invalid WhatsApp number length")

    return clean_target


# Internal Fonnte request
async def _send_fonnte_request(
    client: httpx.AsyncClient,
    target_wa: str,
    message: str,
) -> dict:

    if not settings.FONNTE_TOKEN:
        return {
            "status": False,
            "reason": "TOKEN_NOT_CONFIGURED",
        }

    try:
        clean_target = normalize_whatsapp_number(target_wa)

        response = await client.post(
            settings.FONNTE_API_URL,
            headers={
                "Authorization": settings.FONNTE_TOKEN,
            },
            data={
                "target": clean_target,
                "message": message,
            },
        )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            logger.error("Fonnte returned an invalid JSON response")

            return {
                "status": False,
                "reason": "INVALID_RESPONSE",
            }

        if not isinstance(data, dict):
            return {
                "status": False,
                "reason": "INVALID_RESPONSE",
            }

        return data

    except ValueError as exc:
        logger.warning("Invalid WhatsApp target: %s", exc)

        return {
            "status": False,
            "reason": "INVALID_TARGET",
        }

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Fonnte HTTP error. Status: %s",
            exc.response.status_code,
        )

        return {
            "status": False,
            "reason": "HTTP_ERROR",
            "status_code": exc.response.status_code,
        }

    except httpx.RequestError:
        logger.exception("Fonnte connection failed")

        return {
            "status": False,
            "reason": "CONNECTION_ERROR",
        }


# Public Fonnte sender
async def send_fonnte_message(
    target_wa: str,
    message: str,
) -> dict:

    if not settings.FONNTE_TOKEN:
        logger.warning(
            "Fonnte token is not configured. Message was not sent."
        )

        return {
            "status": False,
            "reason": "TOKEN_NOT_CONFIGURED",
        }

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
    ) as client:
        return await _send_fonnte_request(
            client,
            target_wa,
            message,
        )


# Broadcast worker
async def _broadcast_async(
    users: list,
    meal_key: str,
) -> None:

    success_count = 0
    failed_count = 0

    for user_id, user_name, phone_number in users:
        try:
            message = build_whatsapp_message(
                user_name,
                meal_key,
            )

            # Gunakan public sender agar bisa di-mock saat testing.
            # Pemeriksaan FONNTE_TOKEN tetap dilakukan di sender ini.
            result = await send_fonnte_message(
                phone_number,
                message,
            )

            if (
                isinstance(result, dict)
                and result.get("status") is True
            ):
                success_count += 1
            else:
                failed_count += 1

                reason = (
                    result.get("reason", "PROVIDER_REJECTED")
                    if isinstance(result, dict)
                    else "INVALID_RESPONSE"
                )

                logger.warning(
                    "Reminder delivery failed for user ID %s. Reason: %s",
                    user_id,
                    reason,
                )

        except Exception:
            failed_count += 1

            logger.exception(
                "Unexpected broadcast error for user ID %s",
                user_id,
            )

    logger.info(
        "Broadcast completed. Meal: %s | Success: %s | Failed: %s",
        meal_key,
        success_count,
        failed_count,
    )


def trigger_scheduled_broadcast(meal_key: str) -> None:
    """
    Synchronous APScheduler entry point.
    Creates one event loop for the entire broadcast.
    """

    if meal_key not in MEAL_TEMPLATES:
        logger.error("Unknown meal key: %s", meal_key)
        return

    db: Session = SessionLocal()

    try:
        active_users = (
            db.query(User.id, User.nama, User.no_wa)
            .filter(User.is_alarm_active.is_(True))
            .all()
        )

        users = [
            (user.id, user.nama, user.no_wa)
            for user in active_users
            if user.no_wa
        ]

    except Exception:
        logger.exception(
            "Failed to retrieve active users for %s",
            meal_key,
        )
        return

    finally:
        db.close()

    logger.info(
        "Starting %s broadcast for %s active users",
        meal_key,
        len(users),
    )

    if not users:
        logger.info("No active users found. Broadcast skipped.")
        return

    try:
        asyncio.run(
            _broadcast_async(users, meal_key)
        )

    except Exception:
        logger.exception(
            "Broadcast execution failed for %s",
            meal_key,
        )


# Scheduler initialization
def init_scheduler() -> BackgroundScheduler:

    scheduler = BackgroundScheduler(
        timezone=reminder_config.MEAL_TIMEZONE,
    )

    for meal_key in MEAL_ORDER:

        hour, minute = reminder_config.hour_minute(
            meal_key,
        )

        scheduler.add_job(
            trigger_scheduled_broadcast,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
                timezone=reminder_config.MEAL_TIMEZONE,
            ),
            args=[meal_key],
            id=f"alarm_{meal_key}",
            name=JOB_NAMES[meal_key],
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

    return scheduler
