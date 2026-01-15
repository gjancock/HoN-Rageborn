import time
import threading
import win32gui
import win32process
import psutil


class GameCrashedError(RuntimeError):
    """Raised when the game window disappears or crashes."""
    pass


def hwnd_exists(hwnd: int) -> bool:
    """
    Returns True if HWND still exists and its process is alive.
    """
    if not win32gui.IsWindow(hwnd):
        return False

    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.pid_exists(pid)
    except Exception:
        return False


def start_hwnd_watchdog(
    hwnd: int,
    stop_event: threading.Event,
    crash_event: threading.Event,
    interval: float = 0.5,
):
    """
    Starts a background thread that monitors HWND existence.
    If the HWND disappears, STOP_EVENT is set and GameCrashedError is raised.
    """

    def _watch():
        while not stop_event.is_set():
            if not hwnd_exists(hwnd):
                crash_event.set()
                stop_event.set()
                return

            time.sleep(interval)

    t = threading.Thread(
        target=_watch,
        name="HWND-Watchdog",
        daemon=True
    )
    t.start()
    return t
