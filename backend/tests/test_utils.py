import pytest
from fastapi import HTTPException

from app.utils import clean_wa, get_utcnow_naive, get_wa_candidates, normalize_wa


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("081234567890", "6281234567890"),
        ("6281234567890", "6281234567890"),
        ("+62 812-3456-7890", "6281234567890"),
        ("81234567890", "6281234567890"),
    ],
)
def test_normalize_wa_formats_to_62(raw, expected):
    assert normalize_wa(raw) == expected


@pytest.mark.parametrize("raw", ["08123", "abc", "", "0000"])
def test_normalize_wa_rejects_invalid_numbers(raw):
    with pytest.raises(HTTPException) as exc_info:
        normalize_wa(raw)
    assert exc_info.value.status_code == 400


def test_clean_wa_removes_spaces_and_dashes():
    assert clean_wa(" 0812-3456 7890 ") == "081234567890"


def test_get_wa_candidates_covers_local_and_country_format():
    candidates = get_wa_candidates("081234567890")
    assert "081234567890" in candidates
    assert "6281234567890" in candidates


def test_get_utcnow_naive_returns_datetime():
    assert get_utcnow_naive() is not None
