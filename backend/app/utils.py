from datetime import datetime, timezone
import re
from fastapi import HTTPException, status

# Karakter kontrol (newline, tab, null, dll) tidak pernah valid di input teks.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_MULTI_SPACE = re.compile(r"\s+")

# Nama orang: huruf (termasuk unicode), angka, spasi, titik, koma,
# apostrof (O'Brien), dan tanda hubung (Aisyah-Nur).
_NAME_ALLOWED_EXTRA = set(" .,'-")
_PHONE_ALLOWED = set("0123456789+-(). ")


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


def sanitize_person_name(value: str, *, field_label: str = "Nama") -> str:
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} harus berupa teks.",
        )

    cleaned = _CONTROL_CHARS.sub(" ", value).strip()
    cleaned = _MULTI_SPACE.sub(" ", cleaned)

    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} tidak boleh kosong.",
        )

    for char in cleaned:
        if char.isalpha() or char.isdigit() or char in _NAME_ALLOWED_EXTRA:
            continue
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{field_label} hanya boleh berisi huruf, angka, spasi, titik, "
                "koma, apostrof, dan tanda hubung."
            ),
        )

    if len(cleaned) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} minimal 2 karakter.",
        )
    if len(cleaned) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} maksimal 100 karakter.",
        )

    return cleaned


def sanitize_phone_input(value: str) -> str:
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nomor WhatsApp harus berupa teks.",
        )

    cleaned = _CONTROL_CHARS.sub("", value).strip()
    for char in cleaned:
        if char not in _PHONE_ALLOWED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nomor WhatsApp hanya boleh berisi angka dan simbol + - ( ) .",
            )
    return cleaned


def mask_phone(no_wa: str) -> str:
    digits = re.sub(r"\D", "", no_wa or "")
    if not digits:
        return ""
    if len(digits) <= 6:
        return "*" * len(digits)
    hidden = max(2, len(digits) - 8)
    return f"{digits[:4]}{'*' * hidden}{digits[-4:]}"


def sanitize_simple_text(value: str, *, max_length: int = 50, field_label: str = "Nilai") -> str:
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} harus berupa teks.",
        )
    cleaned = _CONTROL_CHARS.sub("", value).strip()
    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} maksimal {max_length} karakter.",
        )
    if re.search(r"[<>]", cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} tidak boleh mengandung karakter < atau >.",
        )
    return cleaned
