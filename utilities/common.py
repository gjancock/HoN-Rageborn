import os
import sys
import time
import core.state as state

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def wait(seconds):
    time.sleep(seconds)

def interruptible_wait(seconds, step=0.05):
    end = time.time() + seconds
    while time.time() < end:
        if state.STOP_EVENT.is_set():
            return
        time.sleep(step)