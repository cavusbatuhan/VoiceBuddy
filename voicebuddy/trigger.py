"""Trigger: wait until the user wants to speak or a timer ends."""

import json
import sys
import time

import keyboard
import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

from voicebuddy.audio import BLOCK_SECONDS, SAMPLE_RATE
from voicebuddy.skills import timer_is_due

# The key that starts a recording. It works even when another window is in front.
HOTKEY = "f9"
# The small Turkish Vosk model. It is not in git; see the README for the download.
WAKE_MODEL_PATH = "models/vosk-tr"


def wait_for_hotkey():
    """Wait for the hotkey or for a timer to end. Return "user" or "timer"."""
    print(f"Press {HOTKEY.upper()}, then speak (Ctrl+C to quit): ")
    while True:
        if timer_is_due(time.time()):
            return "timer"
        # keyboard.wait() would block here and the timers could not be checked.
        # is_pressed only asks "is the key down right now?".
        if keyboard.is_pressed(HOTKEY):
            return "user"
        # Sleep a little so the loop does not keep the processor busy.
        # The sleep is short so that a quick tap is not missed between two checks.
        time.sleep(0.02)


def load_wake_model():
    """Load the Vosk model. This is slow, so call it once and reuse the result."""
    # Vosk prints many log lines while loading; -1 turns them off.
    SetLogLevel(-1)
    return Model(WAKE_MODEL_PATH)


def wait_for_wake_word(model, wake_word):
    """Listen for the wake word or for a timer to end. Return "user" or "timer"."""
    # A new recognizer each time, so nothing from the last turn is left in it.
    # It may answer with any Turkish word. Measured: when it was only allowed
    # to answer with the wake word, it heard the wake word in normal talk too.
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    block_size = int(SAMPLE_RATE * BLOCK_SECONDS)

    print(f'Say "{wake_word}", then speak (Ctrl+C to quit): ')
    # Vosk wants raw 16-bit bytes, so this stream is "raw" and "int16".
    # Leaving the "with" block closes the microphone, so the recording can open it.
    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        while True:
            if timer_is_due(time.time()):
                return "timer"

            # Reading one block takes 0.1 s, so the timers are checked that often.
            data, overflowed = stream.read(block_size)
            # AcceptWaveform returns True when the speaker has paused.
            if recognizer.AcceptWaveform(bytes(data)):
                heard = json.loads(recognizer.Result())["text"]
            else:
                # Still speaking: look at the words guessed so far, to react fast.
                heard = json.loads(recognizer.PartialResult())["partial"]

            # Compare whole words, so "pusulayı" does not count as "pusula".
            if wake_word in heard.split():
                return "user"


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.trigger pusula
    wait_for_wake_word(load_wake_model(), sys.argv[1])
    print("Wake word heard.")
