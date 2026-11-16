"""Speech-to-text: turn recorded audio into Turkish text."""

import sys

import soundfile as sf
from faster_whisper import WhisperModel

MODEL_SIZE = "base"  # chosen by benchmark: as accurate as small, 3 times faster


def load_model(size):
    """Load a Whisper model. This is slow, so call it once and reuse the result."""
    # int8 stores the model weights as small integers: less memory, faster on CPU.
    return WhisperModel(size, device="cpu", compute_type="int8")


def transcribe(samples, model):
    """Return the Turkish text spoken in the samples (16 kHz, 1-D float32 array)."""
    segments, info = model.transcribe(samples, language="tr")

    # Whisper returns the speech in pieces (segments). The real work happens
    # while we loop over them, so we join them here into one string.
    text = ""
    for segment in segments:
        text += segment.text
    return text.strip()


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.stt recording.wav
    samples, sample_rate = sf.read(sys.argv[1], dtype="float32")
    model = load_model(MODEL_SIZE)
    print(transcribe(samples, model))
