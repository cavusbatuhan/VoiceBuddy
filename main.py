"""VoiceBuddy main loop. For now it is a parrot: it repeats what it hears."""

from voicebuddy.audio import record_until_silence
from voicebuddy.stt import MODEL_SIZE, load_model, transcribe
from voicebuddy.tts import speak


def main():
    # Loading the model is slow, so do it once before the loop starts.
    print("Loading the speech model...")
    model = load_model(MODEL_SIZE)

    while True:
        input("Press Enter, then speak (Ctrl+C to quit): ")
        samples = record_until_silence()
        text = transcribe(samples, model)
        print(f"You said: {text}")
        speak(text)


if __name__ == "__main__":
    main()
