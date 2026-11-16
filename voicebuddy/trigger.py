"""Trigger: wait until the user wants to speak or a timer ends."""

import msvcrt
import time

from voicebuddy.skills import timer_is_due


def wait_for_trigger():
    """Wait for Enter or for a timer to end. Return "user" or "timer"."""
    print("Press Enter, then speak (Ctrl+C to quit): ")
    while True:
        if timer_is_due(time.time()):
            return "timer"
        # input() would block here and the timers could not be checked.
        # kbhit only asks "is a key waiting?", getwch then reads that key.
        if msvcrt.kbhit() and msvcrt.getwch() == "\r":
            return "user"
        # Sleep a little so the loop does not keep the processor busy.
        time.sleep(0.1)
