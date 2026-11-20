import pytest

from app.reminder_config import (
    BREAKFAST_TIME,
    DINNER_TIME,
    LUNCH_TIME,
    ReminderConfig,
    reminder_config,
)


def test_time_is_normalized_and_reflected_in_title():
    config = ReminderConfig(breakfast="6:15")

    assert config.MEAL_BREAKFAST_TIME == "06:15"
    assert config.hour_minute("breakfast") == (6, 15)
    assert "06:15 WIB" in config.title_for("breakfast")


def test_invalid_time_is_rejected_with_clear_message():
    with pytest.raises(ValueError, match="di luar rentang"):
        ReminderConfig(lunch="25:99")

    with pytest.raises(ValueError, match="HH:MM"):
        ReminderConfig(dinner="18.30.00")


def test_schedules_payload_uses_configured_times():
    config = ReminderConfig(breakfast="07:30", lunch="12:00", dinner="18:30")

    payload = config.schedules_payload()

    assert [item["id"] for item in payload] == ["breakfast", "lunch", "dinner"]
    assert [item["time"] for item in payload] == [
        "07:30 WIB",
        "12:00 WIB",
        "18:30 WIB",
    ]


def test_templates_follow_configured_time_not_hardcoded_string():
    config = ReminderConfig(dinner="19:45")

    templates = config.build_templates()

    assert "19:45 WIB" in templates["dinner"]["title"]
    assert "18:30 WIB" not in templates["dinner"]["title"]


def test_timezone_label_for_jakarta_and_other_zones():
    assert ReminderConfig(timezone="Asia/Jakarta").timezone_label == "WIB"
    assert ReminderConfig(timezone="Asia/Tokyo").timezone_label == "Asia/Tokyo"


def test_default_config_uses_module_constants():
    """Instance global harus membaca konstanta di blok PENGATURAN JAM."""
    assert reminder_config.meal_times == {
        "breakfast": BREAKFAST_TIME,
        "lunch": LUNCH_TIME,
        "dinner": DINNER_TIME,
    }
