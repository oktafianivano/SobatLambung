
from datetime import datetime
import re
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# ===================== PENGATURAN JAM =====================
# Format HH:MM (24 jam).
BREAKFAST_TIME = "07:30"
LUNCH_TIME = "12:00"
DINNER_TIME = "18:30"

# Timezone configuration.
TIMEZONE = "Asia/Jakarta"
# ==========================================================


MEAL_ORDER: Tuple[str, ...] = (
    "breakfast",
    "lunch",
    "dinner",
)


MEAL_CONTENT = {
    "breakfast": {
        "label": "Sarapan Sehat",
        "description": "Menetralkan asam lambung pagi hari.",
        "title": "🌅 Waktunya Sarapan Sehat",
        "menu": [
            "Bubur ayam tanpa sambal / kuah kuning ringan",
            "Oatmeal dengan pisang matang & madu",
            "Roti gandum panggang + telur rebus",
        ],
        "advice": (
            "Jangan biarkan lambung kosong lebih dari 12 jam sejak malam. "
            "Asam lambung pagi hari dapat mengikis mukosa jika tidak "
            "dinetralisir sarapan rendah asam."
        ),
    },
    "lunch": {
        "label": "Makan Siang Teratur",
        "description": "Mengisi energi dan istirahat kuliah.",
        "title": "☀️ Waktunya Makan Siang",
        "menu": [
            "Nasi putih pulen hangat + sup wortel bayam + ayam suwir kukus",
            "Ikan nila/salmon kukus bumbu kunyit + tahu kukus",
            "Kentang tumbuk (mashed potato) + telur dadar minim minyak",
        ],
        "advice": (
            "Kunyah makanan perlahan (minimal 20-30 kali). "
            "Hindari kopi dingin, minuman bersoda, dan gorengan pedas "
            "di kantin kampus saat istirahat kuliah."
        ),
    },
    "dinner": {
        "label": "Makan Malam Tepat Waktu",
        "description": "Memberi jeda aman sebelum tidur malam.",
        "title": "🌙 Waktunya Makan Malam",
        "menu": [
            "Sup labu siam / wortel hangat + tempe bacem panggang",
            "Nasi tim ayam jamur rendah lemak",
            "Bubur kacang hijau kuah santan sangat encer/tanpa santan",
        ],
        "advice": (
            "Beri jeda minimal 2-3 jam antara makan malam dan waktu tidur "
            "agar asam lambung tidak naik kembali ke esofagus "
            "(mencegah reflux/GERD)."
        ),
    },
}


def _normalize_hhmm(raw: str, field_label: str) -> str:
    """Validate and normalize time into HH:MM format."""

    if not isinstance(raw, str):
        raise ValueError(
            f"{field_label} must be a string in HH:MM format."
        )

    text = raw.strip()

    # Format harus berupa jam:menit.
    if not re.fullmatch(r"\d{1,2}:\d{2}", text):
        raise ValueError(
            f"{field_label} must use HH:MM format. Received: {text}"
        )

    hour_text, minute_text = text.split(":")
    hour = int(hour_text)
    minute = int(minute_text)

    # Format benar, tetapi nilai jam atau menit di luar rentang.
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(
            f"{field_label} di luar rentang waktu yang valid (00:00–23:59)."
        )

    return f"{hour:02d}:{minute:02d}"


class ReminderConfig:
    """Centralized meal reminder configuration."""

    def __init__(
        self,
        breakfast: str = BREAKFAST_TIME,
        lunch: str = LUNCH_TIME,
        dinner: str = DINNER_TIME,
        timezone: str = TIMEZONE,
    ) -> None:

        self.MEAL_BREAKFAST_TIME = _normalize_hhmm(
            breakfast,
            "BREAKFAST_TIME",
        )

        self.MEAL_LUNCH_TIME = _normalize_hhmm(
            lunch,
            "LUNCH_TIME",
        )

        self.MEAL_DINNER_TIME = _normalize_hhmm(
            dinner,
            "DINNER_TIME",
        )

        if not isinstance(timezone, str) or not timezone.strip():
            raise ValueError("Timezone must be a non-empty string.")

        try:
            self._timezone = ZoneInfo(timezone.strip())
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                f"Invalid timezone: {timezone}"
            ) from exc

        self.MEAL_TIMEZONE = timezone.strip()

    @property
    def meal_times(self) -> Dict[str, str]:
        return {
            "breakfast": self.MEAL_BREAKFAST_TIME,
            "lunch": self.MEAL_LUNCH_TIME,
            "dinner": self.MEAL_DINNER_TIME,
        }

    @property
    def timezone_label(self) -> str:
        labels = {
            "Asia/Jakarta": "WIB",
            "Asia/Makassar": "WITA",
            "Asia/Jayapura": "WIT",
        }

        return labels.get(
            self.MEAL_TIMEZONE,
            self.MEAL_TIMEZONE,
        )

    def _validate_meal_key(self, meal_key: str) -> None:
        if meal_key not in MEAL_ORDER:
            raise ValueError(
                f"Unsupported meal key: {meal_key}"
            )

    def hour_minute(self, meal_key: str) -> Tuple[int, int]:
        """Return hour and minute for CronTrigger."""

        self._validate_meal_key(meal_key)

        hour, minute = self.meal_times[meal_key].split(":")

        return int(hour), int(minute)

    def display_time(self, meal_key: str) -> str:
        """Return formatted display time."""

        self._validate_meal_key(meal_key)

        return (
            f"{self.meal_times[meal_key]} "
            f"{self.timezone_label}"
        )

    def title_for(self, meal_key: str) -> str:
        """Generate meal title with dynamic schedule."""

        self._validate_meal_key(meal_key)

        content = MEAL_CONTENT[meal_key]

        return (
            f"{content['title']} "
            f"({self.display_time(meal_key)})"
        )

    def build_templates(self) -> Dict[str, Dict[str, object]]:
        """Build WhatsApp reminder templates."""

        templates = {}

        for key in MEAL_ORDER:
            content = MEAL_CONTENT[key]

            templates[key] = {
                "title": self.title_for(key),
                "menu": list(content["menu"]),
                "advice": content["advice"],
            }

        return templates

    def schedules_payload(self) -> List[Dict[str, str]]:
        """Build frontend schedule response."""

        payload = []

        for key in MEAL_ORDER:
            content = MEAL_CONTENT[key]

            payload.append({
                "id": key,
                "time": self.display_time(key),
                "label": content["label"],
                "description": content["description"],
            })

        return payload


reminder_config = ReminderConfig()
