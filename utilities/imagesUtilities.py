import pyautogui
import time
import os

from utilities.paths import get_launcher_dir
from utilities.common import wait
from utilities.constants import GAME_REGION, CONFIDENCE
from utilities.loggerSetup import setup_logger
from core.parameters import TARGETING_HERO
import pyscreeze

# Initialize Logger
logger = setup_logger()

IMAGE_ROOT = get_launcher_dir() / "images"

def resolve_image_path(image_rel_path: str) -> str:
    """
    Resolve absolute path to a bundled image.
    """
    image_path = IMAGE_ROOT / image_rel_path

    if not image_path.exists():
        logger.error(f"[IMAGE] File does not exist: {image_path}")

    return str(image_path)


def image_exists(image_rel_path, region=None, confidence=None, throwException=False):
    full_path = resolve_image_path(image_rel_path)

    try:
        return pyautogui.locateOnScreen(
            full_path,
            confidence=confidence if confidence is not None else CONFIDENCE,
            region=region if region is not None else GAME_REGION
        ) is not None
    except pyautogui.ImageNotFoundException:
        return False if throwException else None

    
def any_image_exists(image_rel_paths, region=None, confidence=None):
    """
    Check if ANY image (relative path) exists on screen.
    """
    for img in image_rel_paths:
        if image_exists(img, region=region, confidence=confidence):
            return True
    return False


def image_exists_in_any_region(image_path, regions):
    """
    Returns True if image is found in ANY region.
    Stops scanning immediately once found.
    """
    for region in regions:
        if image_exists(image_path, region=region):
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
    
def find_and_click(
    image,
    rightClick=False,
    doubleClick=False,
    region=None,
    confidence=CONFIDENCE,
    log_missing=False
):
    try:
        image_path = resolve_image_path(image)

        location = pyautogui.locateCenterOnScreen(
            image_path,
            confidence=confidence,
            region=region
        )

        if not location:
            return False

        pyautogui.moveTo(location, duration=0.15)

        if doubleClick:
            pyautogui.doubleClick()
        elif rightClick:
            pyautogui.rightClick()
        else:
            pyautogui.click()

        return True

    except (pyautogui.ImageNotFoundException,
            pyscreeze.ImageNotFoundException):
        if log_missing:
            logger.debug(f"[IMAGE] Not found: {image}")
        return False

    except OSError as e:
        logger.error(f"[IMAGE] Failed to load image file: {image}")
        logger.error(str(e))
        return False

    except Exception:
        logger.exception(f"[IMAGE] Unexpected error while finding {image}")
        return False

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

    full_click_path = resolve_image_path(click_image_rel_path)

    full_wait_paths = [
        resolve_image_path(p)
        for p in wait_image_rel_path
    ]


    start = time.time()

    while time.time() - start < timeout:

        # Stop condition (OR logic)
        if any_image_exists(wait_image_rel_path, region):
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