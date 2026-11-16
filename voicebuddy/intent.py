"""Intent recognition: decide which command a sentence means."""

import json
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

INTENTS_FILE = "data/intents.json"
# Below this confidence the sentence is treated as "not a command".
# Measured: unseen commands scored 0.61 or more, unrelated sentences mostly 0.33 or less.
THRESHOLD = 0.5


def load_intents():
    """Read intents.json and return it as a dictionary: intent name -> its details."""
    with open(INTENTS_FILE, encoding="utf-8") as file:
        return json.load(file)


def train():
    """Train the intent model on the example sentences and return it."""
    intents = load_intents()

    # Flatten the file into two lists: a sentence and the intent it belongs to.
    sentences = []
    labels = []
    for name, intent in intents.items():
        for example in intent["examples"]:
            sentences.append(example)
            labels.append(name)

    # TF-IDF turns a sentence into numbers by counting pieces of 2 to 4 letters.
    # Letter pieces tolerate Turkish suffixes: "youtube'u" and "youtubu" share most.
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    # Logistic regression learns which letter pieces point to which intent.
    # A higher C trusts the examples more, so the probabilities are less flat.
    classifier = LogisticRegression(C=10)

    model = make_pipeline(vectorizer, classifier)
    model.fit(sentences, labels)
    return model


def predict(text, model):
    """Return the most likely intent name and its confidence (0 to 1)."""
    # predict_proba gives one probability per intent, in the order of classes_.
    probabilities = model.predict_proba([text])[0]
    best = probabilities.argmax()
    return model.classes_[best], probabilities[best]


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.intent "youtube'u aç"
    model = train()
    name, confidence = predict(sys.argv[1], model)
    print(f"{name} ({confidence:.2f})")
