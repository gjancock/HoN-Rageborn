import core.state as state
from datetime import datetime

def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def reset_endless_ui(duration_var, iteration_var):
    """
    Reset endless-mode runtime + UI text.
    """
    state.reset_endless_stats()
    duration_var.set("Duration: 00:00:00")
    iteration_var.set("Iterations completed: 0")


def update_iteration_ui(duration_var, iteration_var):
    """
    Called when a cycle completes.
    """
    state.increment_iteration()

    iterations = state.get_iteration_count()
    elapsed = state.get_elapsed_seconds()

    iteration_var.set(f"Iterations completed: {iterations}")
    duration_var.set(f"Duration: {format_duration(elapsed)}")


def start_endless_ui_refresh(root, duration_var, iteration_var, interval_ms=1000):
    """
    Periodically refresh UI from state (Tk-safe polling).
    """

    def _tick():
        iterations = state.get_iteration_count()
        elapsed = state.get_elapsed_seconds()

        iteration_var.set(f"Iterations completed: {iterations}")
        duration_var.set(f"Duration: {format_duration(elapsed)}")

        root.after(interval_ms, _tick)

    _tick()
