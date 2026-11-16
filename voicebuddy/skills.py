"""Skills: the things the assistant can do. Each one returns the answer as text."""

import os


def say(intent, text):
    """Answer with the fixed sentence of the intent (greeting, goodbye)."""
    return intent["answer"]


def open_target(intent, text):
    """Open the website or program of the intent."""
    # os.startfile works like the Windows "Run" box: a web address opens
    # in the browser, a program name such as "calc" starts that program.
    try:
        os.startfile(intent["target"])
    except OSError:
        # Windows could not find it, for example Excel is not installed.
        return "Bunu açamadım."
    return intent["answer"]


# The "skill" field in intents.json picks one of these functions.
SKILLS = {
    "say": say,
    "open": open_target,
}
