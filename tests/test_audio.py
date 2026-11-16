"""Tests for the recording. No microphone is used: the input stream is replaced by a fake."""

import numpy as np

from voicebuddy import audio


class FakeStream:
    """Stands in for sd.InputStream and returns blocks of a fixed loudness."""

    # The loudness of each block after the warm-up read, in order.
    levels = []

    def __init__(self, **settings):
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, *error):
        pass

    def read(self, frames):
        # The first read is the warm-up; after the list ends there is silence.
        index = self.reads - 1
        self.reads += 1
        level = 0.0
        if 0 <= index < len(FakeStream.levels):
            level = FakeStream.levels[index]
        return np.full((frames, 1), level, dtype="float32"), False


def test_only_silence_returns_no_samples(monkeypatch):
    monkeypatch.setattr(audio.sd, "InputStream", FakeStream)
    monkeypatch.setattr(audio, "MAX_SECONDS", 1.0)
    FakeStream.levels = []
    assert len(audio.record_until_silence()) == 0


def test_recording_stops_one_second_after_the_speech(monkeypatch):
    monkeypatch.setattr(audio.sd, "InputStream", FakeStream)
    # Five loud blocks (0.5 s of speech), then silence.
    FakeStream.levels = [0.1] * 5
    samples = audio.record_until_silence()
    # 0.5 s of speech + 1.0 s of silence at 16000 samples per second.
    assert len(samples) == 24000
