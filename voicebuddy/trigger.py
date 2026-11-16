"""Trigger: wait until the user wants to speak or a timer ends."""

import time

import keyboard

from voicebuddy.skills import timer_is_due

# The key that starts a recording. It works even when another window is in front.
HOTKEY = "f9"


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
