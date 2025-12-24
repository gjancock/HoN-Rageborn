import keyboard
import core.state as state
from utilities.loggerSetup import setup_logger

logger = setup_logger()

# not working well; causing program not able to auto loop after iteration
def kill_switch_listener():
    """
    Global hotkey kill-switch.
    Works even when the game window is focused.
    """
    logger.info("[KILL] Kill-switch armed: Ctrl+Shift+Q")

    # This blocks internally, but it's running in its own daemon thread
    keyboard.wait("ctrl+shift+q")

    logger.warning("[KILL] Kill-switch activated!")
    state.STOP_EVENT.set()
