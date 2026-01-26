# ui/endless_controller.py
import threading
import time
import core.state as state

class EndlessController:
    def __init__(self, worker_func):
        self._worker_func = worker_func
        self._thread = None
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        with self._lock:
            if self._running:
                return False  # already running

            self._running = True
            state.reset_endless_stats()

            self._thread = threading.Thread(
                target=self._run,
                daemon=True
            )
            self._thread.start()
            return True

    def _run(self):
        try:
            self._worker_func()
        finally:
            # Ensure controller state is always cleaned up
            with self._lock:
                self._running = False
                self._thread = None

    def stop(self):
        with self._lock:
            self._running = False
        # worker exits naturally via auto_mode_var or STOP_EVENT

    def is_running(self):
        with self._lock:
            return self._running
