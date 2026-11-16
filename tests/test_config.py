"""Tests for the settings file."""

from voicebuddy.config import load_config


def test_trigger_mode_is_a_known_mode():
    trigger = load_config()["trigger"]
    assert trigger["mode"] in ("hotkey", "wake_word")


def test_wake_word_is_one_lowercase_word():
    # The wake word is compared with the lowercase words Vosk returns.
    wake_word = load_config()["trigger"]["wake_word"]
    assert wake_word == wake_word.lower()
    assert len(wake_word.split()) == 1


def test_weather_place_has_a_name_and_coordinates():
    weather = load_config()["weather"]
    assert weather["city"] != ""
    assert -90 <= weather["latitude"] <= 90
    assert -180 <= weather["longitude"] <= 180
