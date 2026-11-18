from fastapi import APIRouter

from app.reminder_config import reminder_config

router = APIRouter()

@router.get("/")
def read_root():
    return {
        "app": "Sobat Lambung API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@router.get("/education/content")
def get_education_content():
    return {
        "gastritis": {
            "title": "Apa Itu Gastritis (Maag)?",
            "description": "Peradangan pada lapisan mukosa lambung yang sering dipicu oleh pola makan tidak teratur, stres akademik, konsumsi NSAID berlebihan, atau infeksi bakteri H. pylori.",
            "symptoms": ["Nyeri ulu hati terasa perih atau terbakar", "Perut kembung dan begah setelah makan sedikit", "Mual, muntah, atau sering bersendawa asam"],
            "triggers_mahasiswa": ["Sering skip sarapan karena kelas pagi", "Minum kopi saat perut masih kosong", "Tidur larut malam (begadang nugas)", "Tingkat stres tinggi menjelang ujian/sidang"]
        },
        "gerd": {
            "title": "Mengenal GERD (Gastroesophageal Reflux Disease)",
            "description": "Kondisi kronis ketika asam lambung dan enzim pencernaan mengalir balik (reflux) ke kerongkongan akibat melemahnya katup sfingter esofagus bawah (LES).",
            "symptoms": ["Sensasi dada terbakar (heartburn)", "Rasa asam atau pahit di pangkal tenggorokan", "Batuk kering kronis dan suara serak di pagi hari", "Sensasi mengganjal saat menelan"],
            "dos_and_donts": {
                "anjuran": ["Makan dengan porsi kecil tapi sering (small frequent meals)", "Beri jeda minimal 2-3 jam setelah makan sebelum rebahan", "Tinggikan posisi kepala saat tidur 15-20 cm"],
                "pantangan": ["Langsung tidur/rebahan setelah makan mie instan malam hari", "Pakaian atau celana yang terlalu ketat menekan perut", "Rokok, alkohol, dan makanan sangat asam/pedas"]
            }
        },
        "food_recommendations": [
            {"category": "Karbohidrat Ramah Lambung", "items": ["Nasi tim / bubur", "Oatmeal matang", "Kentang rebus", "Roti gandum"]},
            {"category": "Protein Rendah Lemak", "items": ["Dada ayam rebus/kukus", "Tahu & tempe kukus/bacem", "Telur rebus", "Ikan nila / gabus"]},
            {"category": "Sayuran Rendah Gas", "items": ["Wortel", "Labu siam", "Bayam hijau muda", "Buncis muda"]},
            {"category": "Buah Rendah Asam", "items": ["Pisang ambon / kepok", "Pepaya matang", "Melon madu", "Alpukat"]}
        ]
    }

@router.get("/schedules")
def get_static_schedules():
    """Jadwal pengingat aktif. Sumbernya ``app.reminder_config`` supaya
    frontend selalu menampilkan jam yang sama dengan yang dipakai scheduler."""
    return reminder_config.schedules_payload()