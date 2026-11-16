"""Measure the intent model on sentences it has never seen.

Run from the project folder: python -m scripts.evaluate_intents
"""

import json

from sklearn.metrics import confusion_matrix

from voicebuddy.intent import THRESHOLD, predict, train

TEST_FILE = "data/intents_test.json"
# The label for "not a command". The model never learns it;
# a prediction becomes "none" when its confidence is below the threshold.
NONE = "none"

with open(TEST_FILE, encoding="utf-8") as file:
    test_sentences = json.load(file)

model = train()

expected = []
predicted = []
mistakes = []
for name, sentences in test_sentences.items():
    for sentence in sentences:
        guess, confidence = predict(sentence, model)
        if confidence < THRESHOLD:
            guess = NONE
        expected.append(name)
        predicted.append(guess)
        if guess != name:
            mistakes.append(f"{sentence} | expected {name}, got {guess} ({confidence:.2f})")

correct = len(expected) - len(mistakes)
percent = 100 * correct / len(expected)
print(f"Accuracy: {correct}/{len(expected)} ({percent:.0f}%)")

print("\nMistakes:")
for mistake in mistakes:
    print(mistake)

# Row = the right answer, column = what the model said.
# Numbers on the diagonal are correct, everything else is a mix-up.
names = list(test_sentences)
matrix = confusion_matrix(expected, predicted, labels=names)

print("\nConfusion matrix (rows: expected, columns: predicted)")
header = " " * 19
for number in range(1, len(names) + 1):
    header += f"{number:3}"
print(header)
for number, name in enumerate(names, start=1):
    row = f"{number:2} {name:16}"
    for count in matrix[number - 1]:
        row += f"{count:3}"
    print(row)
