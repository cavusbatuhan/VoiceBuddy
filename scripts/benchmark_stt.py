"""Compare Whisper model sizes on speed and accuracy with your own voice.

Run from the project folder: python -m scripts.benchmark_stt
"""

import time

import soundfile as sf

from voicebuddy.audio import SAMPLE_RATE, record_until_silence
from voicebuddy.stt import load_model, transcribe

MODEL_SIZES = ["base", "small"]
SENTENCES = [
    "youtube'u aç",
    "saat kaç",
    "bugün hava nasıl",
    "beş dakikalık zamanlayıcı kur",
    "bugün günlerden ne",
    # Longer free-form sentences: these went wrong in the first parrot test.
    "bu söylediklerimin kaçını anlayabiliyorsun",
    "baştan başlıyorum saymaya",
    "bütün kelimeleri doğru anlayamadığını varsayıyorum",
    "kolaydan zora doğru birkaç kelime anlatmaya çalışacağım",
]


def to_words(text):
    """Lowercase the text, drop punctuation and split it into words."""
    text = text.lower()
    for mark in ".,?!":
        text = text.replace(mark, "")
    return text.split()


def count_correct_words(expected, heard):
    """Count how many of the expected words appear in the heard text."""
    heard_words = to_words(heard)
    correct = 0
    for word in to_words(expected):
        if word in heard_words:
            correct += 1
    return correct


# Record every sentence once, so both models get exactly the same audio.
# Each one is also saved as a wav file, so a bad result can be listened to.
recordings = []
for number, sentence in enumerate(SENTENCES, start=1):
    input(f'Press Enter, wait for "Listening...", then say: "{sentence}"')
    samples = record_until_silence()
    sf.write(f"sample_{number}.wav", samples, SAMPLE_RATE)
    recordings.append(samples)

for size in MODEL_SIZES:
    print(f"\n--- {size} ---")
    model = load_model(size)
    total_seconds = 0.0
    total_correct = 0
    total_words = 0

    for sentence, samples in zip(SENTENCES, recordings):
        start = time.perf_counter()
        heard = transcribe(samples, model)
        seconds = time.perf_counter() - start

        total_seconds += seconds
        total_correct += count_correct_words(sentence, heard)
        total_words += len(to_words(sentence))
        print(f"{seconds:5.2f} s | expected: {sentence} | heard: {heard}")

    average = total_seconds / len(SENTENCES)
    print(f"{size}: average {average:.2f} s, {total_correct}/{total_words} words correct")
