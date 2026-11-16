"""Skills: the things the assistant can do. Each one returns the answer as text."""

import os
from datetime import datetime

# Written by hand so the answer is Turkish on every computer.
# datetime.weekday() counts from Monday = 0, so the list starts with Monday.
DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


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


# The "skill" field in intents.json picks one of these functions.
SKILLS = {
    "say": say,
    "open": open_target,
    "time": tell_time,
    "date": tell_date,
}
