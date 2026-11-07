from datetime import datetime, timezone
import re
from fastapi import HTTPException, status

def get_utcnow_naive() -> datetime:
    return datetime.now(timezone.utc)

def clean_wa(no_wa: str) -> str:
    return no_wa.strip().replace(" ", "").replace("-", "")

def normalize_wa(no_wa: str) -> str:
    cleaned = re.sub(r"[\s\-().]", "", no_wa.strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("0"):
        cleaned = "62" + cleaned[1:]
    elif cleaned.startswith("8"):
        cleaned = "62" + cleaned

    if not re.fullmatch(r"628[1-9][0-9]{7,11}", cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format nomor WhatsApp tidak valid. Contoh: 08123456789 atau 628123456789."
        )
    return cleaned

def get_wa_candidates(no_wa: str) -> list[str]:
    cleaned = re.sub(r"[\s\-().]", "", no_wa.strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    candidates = {cleaned}
    if cleaned.startswith("0"):
        candidates.add("62" + cleaned[1:])
    elif cleaned.startswith("62"):
        candidates.add("0" + cleaned[2:])
    elif cleaned.startswith("8"):
        candidates.add("62" + cleaned)
        candidates.add("0" + cleaned)
    return list(candidates)