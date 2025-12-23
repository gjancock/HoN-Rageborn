import threading
import time
import pyautogui
from utilities.loggerSetup import setup_logger
from utilities.constants import VOTE_REGION
from core.state import STOP_EVENT, vote_in_progress, vote_already_cast
from utilities.imagesUtilities import find_and_click, image_exists

# Initialize Logger
logger = setup_logger()

#
def decline_vote_watcher():
    """
    Detects 'vote call' popup and opens it if needed.
    """
    while not STOP_EVENT.is_set():
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