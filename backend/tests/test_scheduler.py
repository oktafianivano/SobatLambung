from app.scheduler import (
    MEAL_TEMPLATES,
    build_reset_otp_message,
    build_whatsapp_message,
)


def test_build_message_contains_user_name_and_title():
    message = build_whatsapp_message("Ivano", "breakfast")
    assert "Ivano" in message
    assert MEAL_TEMPLATES["breakfast"]["title"] in message


def test_build_message_includes_every_menu_item():
    message = build_whatsapp_message("Ivano", "lunch")
    for menu_item in MEAL_TEMPLATES["lunch"]["menu"]:
        assert menu_item in message


def test_unknown_meal_key_falls_back_to_lunch():
    message = build_whatsapp_message("Ivano", "menu-tidak-ada")
    assert MEAL_TEMPLATES["lunch"]["title"] in message


def test_reset_otp_message_contains_code_and_expiry():
    message = build_reset_otp_message("Ivano", "123456", 10)
    assert "123456" in message
    assert "10 menit" in message
