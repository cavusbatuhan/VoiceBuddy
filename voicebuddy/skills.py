"""Skills: the things the assistant can do. Each one returns the answer as text."""

import os
import time
from datetime import datetime

# Written by hand so the answer is Turkish on every computer.
# datetime.weekday() counts from Monday = 0, so the list starts with Monday.
DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]

# Number words are added together: "yirmi beş" is 20 + 5.
NUMBER_WORDS = {
    "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5,
    "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9,
    "on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50,
    "altmış": 60, "yetmiş": 70, "seksen": 80, "doksan": 90,
}
# How many seconds one of each time unit is.
UNIT_SECONDS = {"saniye": 1, "dakika": 60, "saat": 3600}

# The moments (as time.time() values) when the running timers end.
timers = []


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


def format_time(now):
    """Turn a datetime into a sentence such as "Saat 14:05."."""
    # :02d writes the number with two digits, so 5 minutes becomes "05".
    return f"Saat {now.hour:02d}:{now.minute:02d}."


def format_date(now):
    """Turn a datetime into a sentence such as "Bugün 16 Kasım 2026, Pazartesi."."""
    day_name = DAYS[now.weekday()]
    # Months count from 1 but the list counts from 0.
    month_name = MONTHS[now.month - 1]
    return f"Bugün {now.day} {month_name} {now.year}, {day_name}."


def tell_time(intent, text):
    """Say what time it is now."""
    return format_time(datetime.now())


def tell_date(intent, text):
    """Say what the date is today."""
    return format_date(datetime.now())


def unit_seconds(word):
    """Return the seconds of the time unit the word starts with, or 0 if it is not a unit."""
    # startswith tolerates Turkish suffixes: "dakikalık" and "dakikaya" start with "dakika".
    for unit, seconds in UNIT_SECONDS.items():
        if word.startswith(unit):
            return seconds
    return 0


def parse_duration(text):
    """Find a duration in the sentence and return it in seconds, or None if there is none."""
    # Python lowers "İ" to an "i" with an extra dot sign, so replace it by hand first.
    words = text.replace("İ", "i").lower().split()

    total = 0
    number = 0
    for word in words:
        # Whisper adds punctuation: "kur." must become "kur".
        word = word.strip(".,?!")
        seconds = unit_seconds(word)
        if word.isdigit():
            number = int(word)
        elif word in NUMBER_WORDS:
            number += NUMBER_WORDS[word]
        elif seconds > 0:
            # A unit closes the number before it: "5 dakika" adds 5 * 60.
            total += number * seconds
            number = 0
        else:
            # Any other word breaks the number: the "bir" in "bir sayaç" is not a duration.
            number = 0

    if total == 0:
        return None
    return total


def format_duration(seconds):
    """Turn seconds into words such as "1 saat 5 dakika"."""
    hours = seconds // 3600
    minutes = seconds % 3600 // 60
    rest = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} saat")
    if minutes > 0:
        parts.append(f"{minutes} dakika")
    if rest > 0:
        parts.append(f"{rest} saniye")
    return " ".join(parts)


def set_timer(intent, text):
    """Start a timer for the duration said in the sentence."""
    seconds = parse_duration(text)
    if seconds is None:
        return "Ne kadar süre için kurayım?"
    # No thread: only write down when the timer ends. The main loop checks the list.
    timers.append(time.time() + seconds)
    return f"{format_duration(seconds)} sonra haber veririm."


def timer_is_due(now):
    """Remove one finished timer and return True, or return False if none has finished."""
    for end in timers:
        if end <= now:
            timers.remove(end)
            return True
    return False


# The "skill" field in intents.json picks one of these functions.
SKILLS = {
    "say": say,
    "open": open_target,
    "time": tell_time,
    "date": tell_date,
    "timer": set_timer,
}
