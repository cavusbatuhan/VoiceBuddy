"""Tests for the skills. Nothing is really opened: os.startfile is replaced by a fake."""

import os
from datetime import datetime

from voicebuddy.intent import load_intents
from voicebuddy.skills import (
    SKILLS,
    format_date,
    format_duration,
    format_time,
    open_target,
    parse_duration,
    say,
    set_timer,
    timer_is_due,
    timers,
)


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


def test_parse_duration_reads_digits_and_words():
    assert parse_duration("5 dakikalık zamanlayıcı kur") == 300
    assert parse_duration("beş dakika sonra haber ver") == 300


def test_parse_duration_adds_number_words_and_units():
    assert parse_duration("yirmi beş saniye say") == 25
    assert parse_duration("1 saat 30 dakikaya kur") == 5400


def test_parse_duration_handles_whisper_spelling():
    # Whisper starts with a capital letter and ends with a full stop.
    assert parse_duration("İki dakika.") == 120


def test_parse_duration_ignores_a_number_without_a_unit():
    # "bir" belongs to "sayaç" here, only "on saniye" is a duration.
    assert parse_duration("bir sayaç kur on saniye") == 10
    assert parse_duration("zamanlayıcı kur") is None


def test_format_duration_skips_the_empty_parts():
    assert format_duration(300) == "5 dakika"
    assert format_duration(3725) == "1 saat 2 dakika 5 saniye"


def test_set_timer_writes_down_the_end_time():
    timers.clear()
    answer = set_timer({}, "10 saniye say")

    assert answer == "10 saniye sonra haber veririm."
    assert len(timers) == 1
    timers.clear()


def test_set_timer_asks_when_there_is_no_duration():
    timers.clear()
    assert set_timer({}, "zamanlayıcı kur") == "Ne kadar süre için kurayım?"
    assert timers == []


def test_timer_is_due_only_after_the_end_time():
    timers.clear()
    timers.append(100)

    assert timer_is_due(99) is False
    assert timer_is_due(100) is True
    # A finished timer is removed, so it is reported only once.
    assert timer_is_due(101) is False


def test_every_skill_in_intents_file_exists():
    for name, intent in load_intents().items():
        if "skill" in intent:
            assert intent["skill"] in SKILLS, name
