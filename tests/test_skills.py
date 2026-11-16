"""Tests for the skills. Nothing is really opened: os.startfile is replaced by a fake."""

import os
from datetime import datetime

from voicebuddy.intent import load_intents
from voicebuddy.skills import SKILLS, format_date, format_time, open_target, say


def test_say_returns_the_answer():
    intent = {"answer": "Merhaba."}
    assert say(intent, "selam") == "Merhaba."


def test_open_target_opens_the_target(monkeypatch):
    opened = []
    # The fake only writes down what it was asked to open.
    monkeypatch.setattr(os, "startfile", opened.append, raising=False)

    intent = {"target": "https://www.youtube.com", "answer": "YouTube açılıyor."}
    answer = open_target(intent, "youtube'u aç")

    assert opened == ["https://www.youtube.com"]
    assert answer == "YouTube açılıyor."


def test_open_target_says_so_when_it_fails(monkeypatch):
    def fail(target):
        raise FileNotFoundError(target)

    monkeypatch.setattr(os, "startfile", fail, raising=False)

    intent = {"target": "excel", "answer": "Excel açılıyor."}
    assert open_target(intent, "exceli aç") == "Bunu açamadım."


def test_format_time_uses_two_digits():
    # A fixed moment, so the test gives the same result whenever it runs.
    now = datetime(2026, 11, 16, 9, 5)
    assert format_time(now) == "Saat 09:05."


def test_format_date_names_the_month_and_the_day():
    # 16 November 2026 is a Monday.
    now = datetime(2026, 11, 16, 9, 5)
    assert format_date(now) == "Bugün 16 Kasım 2026, Pazartesi."


def test_format_date_on_the_last_day_of_the_year():
    # Checks the ends of both lists: December and Sunday (31 December 2028).
    now = datetime(2028, 12, 31, 23, 59)
    assert format_date(now) == "Bugün 31 Aralık 2028, Pazar."


def test_every_skill_in_intents_file_exists():
    for name, intent in load_intents().items():
        if "skill" in intent:
            assert intent["skill"] in SKILLS, name
