import pytest
from pydantic import ValidationError

from app.reminder_config import ReminderConfig


def test_time_is_normalized_and_reflected_in_title():
    config = ReminderConfig(MEAL_BREAKFAST_TIME="6:15")

    assert config.MEAL_BREAKFAST_TIME == "06:15"
    assert config.hour_minute("breakfast") == (6, 15)
    assert "06:15 WIB" in config.title_for("breakfast")


def test_invalid_time_is_rejected_with_clear_message():
    with pytest.raises(ValidationError):
        ReminderConfig(MEAL_LUNCH_TIME="25:99")

    with pytest.raises(ValidationError):
        ReminderConfig(MEAL_DINNER_TIME="18.30.00")


def test_schedules_payload_uses_configured_times():
    config = ReminderConfig(
        MEAL_BREAKFAST_TIME="07:30",
        MEAL_LUNCH_TIME="12:00",
        MEAL_DINNER_TIME="18:30",
    )

    payload = config.schedules_payload()

    assert [item["id"] for item in payload] == ["breakfast", "lunch", "dinner"]
    assert [item["time"] for item in payload] == [
        "07:30 WIB",
        "12:00 WIB",
        "18:30 WIB",
    ]


def test_templates_follow_configured_time_not_default():
    config = ReminderConfig(MEAL_DINNER_TIME="19:45")

    templates = config.build_templates()

    assert "19:45 WIB" in templates["dinner"]["title"]
    assert "18:30 WIB" not in templates["dinner"]["title"]


def test_timezone_label_for_jakarta_and_other_zones():
    assert ReminderConfig(MEAL_TIMEZONE="Asia/Jakarta").timezone_label == "WIB"
    assert ReminderConfig(MEAL_TIMEZONE="Asia/Tokyo").timezone_label == "Asia/Tokyo"
