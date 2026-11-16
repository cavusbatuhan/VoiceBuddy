"""Tests for the speech. Nothing is played: the voice service is replaced by a fake."""

from voicebuddy import tts


class OfflineCommunicate:
    """Stands in for edge_tts.Communicate when there is no internet."""

    def __init__(self, text, voice):
        pass

    def save_sync(self, path):
        raise OSError("no internet")


def test_speak_returns_quietly_without_internet(monkeypatch, capsys):
    played = []
    monkeypatch.setattr(tts.edge_tts, "Communicate", OfflineCommunicate)
    monkeypatch.setattr(tts.sd, "play", played.append)
    tts.speak("Merhaba.")
    assert played == []
    assert "Could not speak" in capsys.readouterr().out
