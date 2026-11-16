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
