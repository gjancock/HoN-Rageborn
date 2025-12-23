import pyautogui
import time
import os
from utilities.common import resource_path, wait
from utilities.constants import GAME_REGION, BASE_IMAGE_DIR, CONFIDENCE
from utilities.loggerSetup import setup_logger
from core.parameters import TARGETING_HERO

# Initialize Logger
logger = setup_logger()

def image_exists(image_rel_path, region=None, confidence=None, throwException=False):
    full_path = resource_path(os.path.join(BASE_IMAGE_DIR, image_rel_path))
    try:
        return pyautogui.locateOnScreen(
            full_path,
            confidence=confidence if confidence is not None else CONFIDENCE,
            region=region if region is not None else GAME_REGION
        ) is not None
    except pyautogui.ImageNotFoundException:
        if throwException:
            return False
        else:
            return None
    
def any_image_exists(image_rel_paths, region=None, confidence=None):
    for img in image_rel_paths:
        if image_exists(img, region, confidence):
            return True
    return False
    
def wait_until_appears(image_rel_path, timeout=30, region=None, confidence=None, throw=False):
    start = time.time()
    while time.time() - start < timeout:
        if image_exists(image_rel_path, region, confidence):
            return True
        time.sleep(0.3)
    if throw:
        logger.info(f"[APP_ERROR] {image_rel_path} did not appear.")
        raise TimeoutError(f"{image_rel_path} did not appear")
    
def find_and_click(image_rel_path, timeout=10, click=True, doubleClick=False, rightClick=False, region=None):
    """
    Finds an image on screen and clicks it.
    """
    full_path = resource_path(os.path.join(BASE_IMAGE_DIR, image_rel_path))
    start_time = time.time()

    while time.time() - start_time < timeout:
        location = pyautogui.locateCenterOnScreen(
            full_path,
            confidence=CONFIDENCE,
            region=region if region is not None else GAME_REGION
        )

        if location:
            if doubleClick:
                pyautogui.doubleClick(location)

            if click:
                pyautogui.click(location)

            if rightClick:
                pyautogui.rightClick(location)
            
            return True

        time.sleep(0.5)

    logger.info(f"[APP_ERROR] Could not find {image_rel_path}")
    pass

def click_until_image_appears(
    click_image_rel_path,
    wait_image_rel_path,
    timeout=60,
    click_interval=1.0,
    region=None,
    throwWhenTimedout=False
):
    """
    Clicks `click_image_rel_path` repeatedly until ANY image in `wait_image_rel_path` appears.
    """

    # Normalize wait images to list
    if isinstance(wait_image_rel_path, str):
        wait_image_rel_path = [wait_image_rel_path]

    full_click_path = resource_path(
        os.path.join(BASE_IMAGE_DIR, click_image_rel_path)
    )

    full_wait_paths = [
        resource_path(os.path.join(BASE_IMAGE_DIR, p))
        for p in wait_image_rel_path
    ]

    start = time.time()

    while time.time() - start < timeout:

        # Stop condition (OR logic)
        if any_image_exists(full_wait_paths, region):
            #logger.info(f"[INFO] One of {wait_image_rel_path} appeared") # DEBUG
            return True

        try:
            location = pyautogui.locateCenterOnScreen(
                full_click_path,
                confidence=CONFIDENCE,
                region=region if region is not None else GAME_REGION
            )

            if location:
                pyautogui.doubleClick(location)
                logger.info(f"[INFO] Clicking {TARGETING_HERO} hero portraits from selection")
                wait(0.5)

        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(click_interval)

    if throwWhenTimedout:
        logger.info(f"[APP_ERROR] {wait_image_rel_path} did not appear in time.")
        raise TimeoutError(f"{wait_image_rel_path} did not appear in time")

    return False