"""Tests for the intent model. None of these sentences are in intents.json."""

import pytest

from voicebuddy.intent import THRESHOLD, predict, train

model = train()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("YouTube'u açar mısın?", "open_youtube"),
        ("Saat kaç acaba?", "time"),
        ("Bugünün tarihi nedir?", "date"),
        ("Üç dakikalık zamanlayıcı kur.", "timer"),
        ("Hava durumu nasıl?", "weather"),
        ("Hesap makinesini açar mısın?", "open_calculator"),
        ("Selam, naber?", "greet"),
        ("Kapanabilirsin.", "quit"),
    ],
)
def test_command_is_recognized(text, expected):
    name, confidence = predict(text, model)
    assert name == expected
    assert confidence >= THRESHOLD


@pytest.mark.parametrize(
    "text",
    [
        "Dün akşam maç izledim.",
        "Türkiye'nin başkenti neresi?",
        "Bana bir hikaye anlat.",
        "",
    ],
)
def test_unrelated_sentence_is_below_threshold(text):
    name, confidence = predict(text, model)
    assert confidence < THRESHOLD
