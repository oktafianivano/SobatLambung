"""Satu sumber kebenaran untuk jadwal & konten pengingat makan.

Jam pengingat, zona waktu, dan teks pesan diambil dari modul ini supaya
scheduler backend dan endpoint API tidak pernah berbeda. Frontend mengambil
jam dari ``/api/v1/schedules`` yang juga membaca modul ini.

Ubah jam lewat environment variable (lihat ``.env.example``)::

    MEAL_BREAKFAST_TIME=07:30
    MEAL_LUNCH_TIME=12:00
    MEAL_DINNER_TIME=18:30
    MEAL_TIMEZONE=Asia/Jakarta

Catatan desain: template pesan dibangun lewat method, bukan disimpan sebagai
atribut kelas. Kalau disimpan sebagai atribut, judul pesan akan terkunci pada
nilai default saat class dibuat dan tidak ikut berubah ketika env di-override
(inilah sumber bug "07:30 WIB" yang terkirim jam 14:30).
"""

from typing import Dict, List, Tuple

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MEAL_ORDER: Tuple[str, ...] = ("breakfast", "lunch", "dinner")

# Konten yang tidak bergantung pada jam, jadi aman disimpan statis.
MEAL_CONTENT: Dict[str, Dict[str, object]] = {
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
            "Kunyah makanan perlahan (minimal 20-30 kali). Hindari kopi dingin, "
            "minuman bersoda, dan gorengan pedas di kantin kampus saat "
            "istirahat kuliah."
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
            "Beri jeda minimal 2-3 jam antara makan malam dan waktu tidur agar "
            "asam lambung tidak naik kembali ke esofagus (mencegah reflux/GERD)."
        ),
    },
}


class ReminderConfig(BaseSettings):
    """Jadwal pengingat makan yang bisa diatur lewat environment variable."""

    MEAL_BREAKFAST_TIME: str = "07:30"
    MEAL_LUNCH_TIME: str = "12:00"
    MEAL_DINNER_TIME: str = "18:30"
    MEAL_TIMEZONE: str = "Asia/Jakarta"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator(
        "MEAL_BREAKFAST_TIME", "MEAL_LUNCH_TIME", "MEAL_DINNER_TIME"
    )
    @classmethod
    def _normalize_hhmm(cls, value: str) -> str:
        raw = str(value).strip()
        parts = raw.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Jam '{raw}' harus berformat HH:MM (contoh 07:30)"
            )
        try:
            hour, minute = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError(
                f"Jam '{raw}' harus berformat HH:MM (contoh 07:30)"
            ) from exc
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Jam '{raw}' di luar rentang 00:00-23:59")
        return f"{hour:02d}:{minute:02d}"

    @property
    def meal_times(self) -> Dict[str, str]:
        """Peta meal_key -> jam 'HH:MM'."""
        return {
            "breakfast": self.MEAL_BREAKFAST_TIME,
            "lunch": self.MEAL_LUNCH_TIME,
            "dinner": self.MEAL_DINNER_TIME,
        }

    @property
    def timezone_label(self) -> str:
        """Label zona waktu untuk ditampilkan di pesan (WIB untuk Jakarta)."""
        if self.MEAL_TIMEZONE == "Asia/Jakarta":
            return "WIB"
        return self.MEAL_TIMEZONE

    def hour_minute(self, meal_key: str) -> Tuple[int, int]:
        """Ambil jam & menit untuk dipakai CronTrigger."""
        hour, minute = self.meal_times[meal_key].split(":")
        return int(hour), int(minute)

    def display_time(self, meal_key: str) -> str:
        """Jam siap tampil, mis. '07:30 WIB'."""
        return f"{self.meal_times[meal_key]} {self.timezone_label}"

    def title_for(self, meal_key: str) -> str:
        """Judul pesan WhatsApp yang selalu mengikuti jam terbaru."""
        content = MEAL_CONTENT.get(meal_key, MEAL_CONTENT["lunch"])
        return f"{content['title']} ({self.display_time(meal_key)})"

    def build_templates(self) -> Dict[str, Dict[str, object]]:
        """Template pesan lengkap (judul + menu + catatan medis)."""
        templates: Dict[str, Dict[str, object]] = {}
        for key in MEAL_ORDER:
            content = MEAL_CONTENT[key]
            templates[key] = {
                "title": self.title_for(key),
                "menu": content["menu"],
                "advice": content["advice"],
            }
        return templates

    def schedules_payload(self) -> List[Dict[str, str]]:
        """Payload untuk endpoint ``GET /schedules`` yang dipakai frontend."""
        payload: List[Dict[str, str]] = []
        for key in MEAL_ORDER:
            content = MEAL_CONTENT[key]
            payload.append(
                {
                    "id": key,
                    "time": self.display_time(key),
                    "label": str(content["label"]),
                    "description": str(content["description"]),
                }
            )
        return payload


reminder_config = ReminderConfig()
