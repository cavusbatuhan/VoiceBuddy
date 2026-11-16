"""Text-to-speech: turn text into Turkish speech and play it."""

import io
import sys

import edge_tts
import sounddevice as sd
import soundfile as sf

VOICE = "tr-TR-EmelNeural"


def speak(text):
    """Say the text out loud and return when the speech has finished."""
    # Ask the online voice service for the speech. It arrives as MP3 pieces.
    communicate = edge_tts.Communicate(text, VOICE)
    mp3_bytes = b""
    for chunk in communicate.stream_sync():
        if chunk["type"] == "audio":
            mp3_bytes += chunk["data"]

    # Decode the MP3 in memory into raw samples, then play them.
    samples, sample_rate = sf.read(io.BytesIO(mp3_bytes))
    sd.play(samples, sample_rate)
    sd.wait()


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.tts "merhaba"
    speak(sys.argv[1])
