import threading
import time
import pyautogui
from utilities.loggerSetup import setup_logger
from utilities.constants import VOTE_REGION
from utilities.imagesUtilities import find_and_click, image_exists
import core.state as state

# Initialize Logger
logger = setup_logger()

def vote_requester():
    logger.info("[THREAD] Vote watcher thread started")

    while not state.STOP_EVENT.is_set():
        state.SCAN_VOTE_EVENT.set()
        time.sleep(0.25)

    logger.info("[THREAD] Vote watcher thread stopped")

def lobby_message_check_requester():
    logger.info("[THREAD] Message watcher thread started")

    while not state.STOP_EVENT.is_set():
        state.SCAN_LOBBY_MESSAGE_EVENT.set()
        time.sleep(0.25)

    logger.info("[THREAD] Message watcher thread stopped")