"""Satu sumber kebenaran untuk jadwal & konten pengingat makan.

UBAH JAM PENGINGAT HANYA DI BLOK ``PENGATURAN JAM`` DI BAWAH.

Nilai di sini dipakai oleh:

- ``app.scheduler`` -> waktu CronTrigger pengiriman WhatsApp
- judul pesan WhatsApp (otomatis mengikuti jam di sini)
- ``GET /api/v1/schedules`` -> dibaca frontend untuk tampilan dashboard

Tidak ada environment variable untuk jam. Kalau ingin mengubah jadwal,
edit konstanta di bawah lalu deploy ulang. Dengan begitu hanya ada satu
tempat yang bisa jadi sumber kebenaran.
"""

from typing import Dict, List, Tuple

# ===================== PENGATURAN JAM =====================
# Format HH:MM (24 jam). Contoh: "07:30", "12:00", "18:30".
BREAKFAST_TIME = "07:30"
LUNCH_TIME = "12:00"
DINNER_TIME = "18:30"

# Zona waktu jadwal. "Asia/Jakarta" akan ditampilkan sebagai "WIB".
TIMEZONE = "Asia/Jakarta"
# ==========================================================

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


def _normalize_hhmm(raw: str, field_label: str) -> str:
    """Validasi & rapikan ``H:MM`` menjadi ``HH:MM``.

    Sengaja fail-fast saat modul di-import supaya salah ketik (mis. ``7.30``
    atau ``25:99``) langsung kelihatan di log deploy, bukan diam-diam
    menggeser jadwal seperti bug sebelumnya.
    """
    text = str(raw).strip()
    parts = text.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"{field_label} harus berformat HH:MM (contoh 07:30), bukan '{text}'"
        )
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(
            f"{field_label} harus berformat HH:MM (contoh 07:30), bukan '{text}'"
        ) from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(
            f"{field_label} di luar rentang 00:00-23:59: '{text}'"
        )
    return f"{hour:02d}:{minute:02d}"


class ReminderConfig:
    """Jadwal pengingat makan.

    Parameter hanya dipakai untuk pengujian; pemakaian normal cukup memakai
    instance ``reminder_config`` yang membaca konstanta di atas.
    """

    def __init__(
        self,
        breakfast: str = BREAKFAST_TIME,
        lunch: str = LUNCH_TIME,
        dinner: str = DINNER_TIME,
        timezone: str = TIMEZONE,
    ) -> None:
        self.MEAL_BREAKFAST_TIME = _normalize_hhmm(breakfast, "BREAKFAST_TIME")
        self.MEAL_LUNCH_TIME = _normalize_hhmm(lunch, "LUNCH_TIME")
        self.MEAL_DINNER_TIME = _normalize_hhmm(dinner, "DINNER_TIME")
        self.MEAL_TIMEZONE = timezone

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
