import os
import sys
import time
import core.state as state

from utilities.paths import get_launcher_dir

def resource_path(relative_path: str) -> str:
    """
    Resolve a read-only bundled resource path.
    Works for both dev and PyInstaller.
    """
    return str(get_launcher_dir() / relative_path)

def wait(seconds):
    time.sleep(seconds)

def interruptible_wait(seconds, step=0.05):
    end = time.time() + seconds
    while time.time() < end:
        if state.STOP_EVENT.is_set():
            return
        time.sleep(step)