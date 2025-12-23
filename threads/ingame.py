import threading
import time
import pyautogui
from utilities.loggerSetup import setup_logger
from utilities.constants import VOTE_REGION
from utilities.imagesUtilities import find_and_click, image_exists
import core.state as state

# Initialize Logger
logger = setup_logger()

#
def decline_vote_watcher():
    """
    Detects 'vote call' popup and opens it if needed.
    """
    while not state.STOP_EVENT.is_set():
        try:            
            if image_exists("vote-no.png", region=VOTE_REGION):
                #vote_in_progress.set()

                logger.info("[INFO] RED vote button spotted! Declining vote.")
                find_and_click("vote-no.png", region=VOTE_REGION)
                time.sleep(0.8)  # debounce
            
            if image_exists("vote-no-black.png", region=VOTE_REGION):
                #vote_in_progress.set()

                logger.info("[INFO] Black vote button spotted! Declining vote.")
                find_and_click("vote-no-black.png", region=VOTE_REGION)
                time.sleep(0.8)  # debounce

        except Exception as e:
            logger.exception(f"[THREADS ERROR] decline_vote_watcher: {e}")
            pass

        time.sleep(0.25)

def vote_requester():
    logger.info("[THREAD] vote requester started")

    while not state.STOP_EVENT.is_set():
        state.SCAN_VOTE_EVENT.set()
        time.sleep(0.25)

    logger.info("[THREAD] vote requester stopped")

def lobby_message_check_requester():
    logger.info("[THREAD] message check requester started")

    while not state.STOP_EVENT.is_set():
        state.SCAN_LOBBY_MESSAGE_EVENT.set()
        time.sleep(0.25)

    logger.info("[THREAD] message check requester stopped")