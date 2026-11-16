"""Tests for the skills. Nothing is really opened: os.startfile is replaced by a fake."""

import os

from voicebuddy.intent import load_intents
from voicebuddy.skills import SKILLS, open_target, say


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


def test_every_skill_in_intents_file_exists():
    for name, intent in load_intents().items():
        if "skill" in intent:
            assert intent["skill"] in SKILLS, name
