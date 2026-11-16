"""Text-to-speech: turn text into Turkish speech and play it."""

import sys

import edge_tts
import sounddevice as sd
import soundfile as sf

VOICE = "tr-TR-EmelNeural"
# The speech is saved here before it is played. Git ignores *.mp3 files.
SPEECH_FILE = "speech.mp3"


def speak(text):
    """Say the text out loud and return when the speech has finished."""
    # Ask the online voice service for the speech and save it as an MP3 file.
    communicate = edge_tts.Communicate(text, VOICE)
    try:
        # Measured: without internet stream_sync() waits forever,
        # but save_sync() raises an error that can be caught here.
        communicate.save_sync(SPEECH_FILE)
    except (OSError, edge_tts.exceptions.NoAudioReceived):
        # OSError: no internet. NoAudioReceived: the text has nothing to say, like "...".
        # The answer is already printed, so the assistant goes on without a voice.
        print("(Could not speak: no internet or nothing to say.)")
        return

    # Decode the MP3 into raw samples, then play them.
    samples, sample_rate = sf.read(SPEECH_FILE)
    sd.play(samples, sample_rate)
    sd.wait()


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.tts "merhaba"
    speak(sys.argv[1])
