"""VoiceBuddy main loop: listen, understand the command, do it, answer out loud."""

from voicebuddy.audio import record_until_silence
from voicebuddy.intent import THRESHOLD, load_intents, predict, train
from voicebuddy.skills import SKILLS
from voicebuddy.stt import MODEL_SIZE, load_model, transcribe
from voicebuddy.trigger import wait_for_trigger
from voicebuddy.tts import speak


def main():
    # Loading the models is slow, so do it once before the loop starts.
    print("Loading the speech model...")
    speech_model = load_model(MODEL_SIZE)
    intents = load_intents()
    intent_model = train()

    while True:
        reason = wait_for_trigger()
        if reason == "timer":
            # Only this loop speaks, so a timer can never talk over a recording.
            print("VoiceBuddy: Süre doldu.")
            speak("Süre doldu.")
            continue

        samples = record_until_silence()
        text = transcribe(samples, speech_model)
        print(f"You said: {text}")

        name, confidence = predict(text, intent_model)
        intent = intents[name]
        print(f"Intent: {name} ({confidence:.2f})")

        if confidence < THRESHOLD:
            # Not sure enough: do nothing rather than run the wrong command.
            answer = "Bunu anlamadım."
        elif "skill" not in intent:
            # The command is recognized but its skill is not written yet.
            answer = "Bunu henüz yapamıyorum."
        else:
            # Look up the function by its name and call it.
            skill = SKILLS[intent["skill"]]
            answer = skill(intent, text)

        print(f"VoiceBuddy: {answer}")
        speak(answer)

        if name == "quit" and confidence >= THRESHOLD:
            break


if __name__ == "__main__":
    main()
