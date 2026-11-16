"""VoiceBuddy main loop: listen, understand the command, do it, answer out loud."""

import sounddevice as sd

from voicebuddy.audio import record_until_silence
from voicebuddy.chat import ask_llm
from voicebuddy.config import load_config
from voicebuddy.intent import THRESHOLD, load_intents, predict, train
from voicebuddy.skills import SKILLS
from voicebuddy.stt import MODEL_SIZE, load_model, transcribe
from voicebuddy.trigger import load_wake_model, wait_for_hotkey, wait_for_wake_word
from voicebuddy.tts import speak


def main():
    # Loading the models is slow, so do it once before the loop starts.
    print("Loading the speech model...")
    speech_model = load_model(MODEL_SIZE)
    intents = load_intents()
    intent_model = train()

    trigger = load_config()["trigger"]
    use_wake_word = trigger["mode"] == "wake_word"
    if use_wake_word:
        wake_model = load_wake_model()

    while True:
        if use_wake_word:
            reason = wait_for_wake_word(wake_model, trigger["wake_word"])
        else:
            reason = wait_for_hotkey(trigger["hotkey"])
        if reason == "timer":
            # Only this loop speaks, so a timer can never talk over a recording.
            print("VoiceBuddy: Süre doldu.")
            speak("Süre doldu.")
            continue

        samples = record_until_silence()
        if len(samples) == 0:
            print("I heard nothing.")
            continue
        text = transcribe(samples, speech_model)
        print(f"You said: {text}")
        if text == "":
            # Nothing was heard, so there is nothing to answer.
            continue

        name, confidence = predict(text, intent_model)
        intent = intents[name]
        print(f"Intent: {name} ({confidence:.2f})")

        if confidence < THRESHOLD:
            # Not sure enough to run a command: treat the sentence as chat.
            # Without an API key this answers "Bunu anlamadım.".
            answer = ask_llm(text)
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
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C: leave quietly instead of printing an error.
        print("Bye.")
    except sd.PortAudioError as error:
        # The microphone or the speakers could not be opened.
        print(f"Audio device problem: {error}")
        print("Check that a microphone and speakers are connected, then start again.")
