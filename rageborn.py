import pyautogui
import cv2
import numpy as np
import time
import os
from pathlib import Path

# Safety: Move mouse to top-left to abort
pyautogui.FAILSAFE = True

# Program Settings
BASE_IMAGE_DIR = "images"
CONFIDENCE = 0.75  # Adjust if detection fails
TARGETING_HERO = "Bubbles"

# Mouse/Keyboard Input Settings
pyautogui.PAUSE = 0.3

#
def image_exists(image_name, region=None, confidence=None):
    image_path = os.path.join(BASE_IMAGE_DIR, image_name)
    try:
        return pyautogui.locateOnScreen(
            image_path,
            confidence=confidence if confidence is not None else CONFIDENCE,
            region=region
        ) is not None
    except pyautogui.ImageNotFoundException:
        return False
    
def any_image_exists(image_names, region=None, confidence=None):
    for img in image_names:
        if image_exists(img, region, confidence):
            return True
    return False
    
def wait_until_appears(image_name, timeout=30, region=None, confidence=None, throw=False):
    start = time.time()
    while time.time() - start < timeout:
        if image_exists(image_name, region, confidence):
            return True
        time.sleep(0.3)
    if throw:
        raise TimeoutError(f"{image_name} did not appear")

def wait_until_disappears(image_name, timeout=30, region=None, confidence=None):
    start = time.time()
    while time.time() - start < timeout:
        if not image_exists(image_name, region, confidence):
            return True
        time.sleep(0.3)
    raise TimeoutError(f"{image_name} did not disappear")

def find_and_click(image_name, timeout=10, click=True, doubleClick=False, rightClick=False):
    """
    Finds an image on screen and clicks it.
    """
    image_path = os.path.join(BASE_IMAGE_DIR, image_name)
    start_time = time.time()

    while time.time() - start_time < timeout:
        location = pyautogui.locateCenterOnScreen(
            image_path,
            confidence=CONFIDENCE
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

    print(f"[ERROR] Could not find {image_name}")
    return False

def click_until_image_appears(
    click_image,
    wait_image,
    timeout=60,
    click_interval=1.0,
    region=None,
    throwWhenTimedout=False
):
    """
    Clicks `click_image` repeatedly until `wait_image` appears.
    """

    #HEROES_PATH = Path(BASE_IMAGE_DIR) / "heroes" / TARGETING_HERO #TODO: Dynamic hero to be choosen
    click_path = os.path.join(BASE_IMAGE_DIR, click_image)
    start = time.time()

    while time.time() - start < timeout:

        # Stop condition
        if any_image_exists(wait_image, region):
            print(f"[OK] {wait_image} hero selected")
            return True

        try:
            location = pyautogui.locateCenterOnScreen(
                click_path,
                confidence=CONFIDENCE,
                region=region
            )

            if location:
                pyautogui.doubleClick(location)
                print(f"Clicked {click_image}")

        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(click_interval)
    if throwWhenTimedout == True:
        raise TimeoutError(f"{wait_image} did not appear in time")
    else:
        return False

def type_text(text, enter=False):
    pyautogui.write(text, interval=0.05)
    if enter:
        pyautogui.press("enter")

def wait(seconds):
    time.sleep(seconds)

#
def account_Login(username, password):
    wait(3)

    while True:
        # do nothing until found username-field.png
        if image_exists("username-field.png"):
            # Click username field
            find_and_click("username-field.png")
            break
        
    type_text(username)

    # Click password field (reuse if same)
    pyautogui.press("tab")
    type_text(password, enter=True)
    print("Waiting account to login...")    
    wait(3)

def prequeue():
    # Queue options
    find_and_click("play-button.png")
    print("PLAY button clicked!")
    wait(3)

def startQueue():
    while True:
        if not image_exists("matchmaking-disabled.png"):
            break
        else:
            print("Matchmaking Disabled, waiting connection...")
            wait(1)
        wait(0.5)

    find_and_click("enter-queue-button.png")
    print("Start Queue!")
    print("Waiting to get match.. 300sec timeout")

    while True:
        if image_exists("message-taken-too-long.png", None):
            wait(2)
            print("waiting taken too long message showed!")
            find_and_click("message-ok.png")
            print("dismiss message pop")

        if image_exists("foc-role-info.png"):
            print("Enter match! FOC role showing!")
            wait(0.5)
            break

        wait(2)

def pickingPhase():
    find_and_click("foc-role-info.png")
    print("Selecting hero")
    wait(3)
    
    if click_until_image_appears("picking-phase-bubbles.png", ["picking-phase-bubbles-self-portrait-legion.png","picking-phase-bubbles-self-portrait-hellbourne.png"], 60, 0.5) == True:
        print("waiting to get in game")
        return True
    else:
        print("Targetted hero banned! Exiting")
        return False

def ingame():
    # Configuration
    side="legion"

    #TODO: clean up until use case happened
    #while True:
    #    if not wait_until_appears("abandon-match-message.png", 3, None, 1):
    #        break
    #    else:
    #        return # Quit this function

    if wait_until_appears("ingame-top-left-menu.png", 150):
        print("in game seeing fountain!")
        wait(1.5)
    else:
        print("Couldn't see emotes button, perhaps we have returned to lobby?")
        if image_exists("abandon-match-message.png", None, 1):            
            return

    # check team side 
    pyautogui.keyDown("x")
    if image_exists("scoreboard-legion.png"):
        print("We are on Legion side!")
        side="legion"
    else:
        print("We are on Hellbourne side!")
        side="hellbourne"
    wait(2)
    pyautogui.keyUp("x")
    wait(0.5)

    # open ingame shop
    pyautogui.press("b")
    print("Open ingame shop")
    wait(0.5)
    # locate to initiation icon
    find_and_click("ingame-shop-initiation-icon.png")
    wait(0.5)
    # find hatcher
    # right click hatcher
    find_and_click("ingame-shop-hatcher-icon.png", 2, False, False, True)
    print("Bought Hatcher!")
    wait(0.5)
    find_and_click("ingame-shop-hatcher-icon.png", 2, False, False, True)
    print("Bought Hatcher!")
    wait(0.5)
    find_and_click("ingame-shop-hatcher-icon.png", 2, False, False, True)
    print("Bought Hatcher!")
    wait(0.5)        
    # close ingame shop
    pyautogui.press("esc")
    print("Close ingame shop")
    wait(2.5)
    # mouse cursor to team mid tower
    # alt+t and click to team mid tower
    # mouse cursor to enemy mid tower
    # right click to enemy mid tower

    while True:
        match side:
            case "legion":
                print("Applying Legion coordinate!")
                pyautogui.moveTo(831, 790, duration=0.3)
                wait(0.5)
                pyautogui.hotkey("alt", "t")
                wait(0.5)
                pyautogui.click()
                wait(3.5)            
                pyautogui.moveTo(850, 771, duration=0.3)
                wait(0.5)
                pyautogui.rightClick()
                wait(0.5)
                pyautogui.click()

            case "hellbourne":
                print("Applying Hellbourne coordinate!")
                pyautogui.moveTo(850, 771, duration=0.3)            
                wait(0.5)
                pyautogui.hotkey("alt", "t")
                wait(0.5)
                pyautogui.click()
                wait(3.5)
                pyautogui.moveTo(831, 790, duration=0.3)
                print("cursor moving to enemy tower")
                wait(0.5)
                pyautogui.rightClick()
                wait(0.5)
                pyautogui.click()
    
        # TODO: spam taunt (need to calculate or know already ready tower)    
        # TODO: death recap or respawn time show then stop spam

        wait(3)
        print("Waiting to get kick by the team...")
        
        if image_exists("vote-no.png"):
            print("See RED vote button! Decline whatever shit it is..")
            wait(1)
            find_and_click("vote-no.png")

        if image_exists("vote-no-black.png"):
            print("See BLACK vote button! Decline whatever shit it is..")
            wait(1)
            find_and_click("vote-no-black.png")

        if image_exists("not-a-host-message.png"):
            break

        if image_exists("cancelled-match-message.png"):
            break

        if image_exists("game-has-ended-message.png"):
            break

        if image_exists("kicked-message.png"):
            break

#
def main(username, password):
    print("Rageborn started...")

    # Example: Open program by clicking icon
    find_and_click("app-icon.png", 10, True, True)
    print("Waiting Jokevio load up...")
    #wait(10)

    # Account Login manually
    account_Login(username, password)

    #
    prequeue()

    #
    startQueue()    
    
    #    
    if pickingPhase():       
        ingame()
    else:
        return
    
    #
    print("We are in the game lobby!")
    wait(0.5)
    if image_exists("message-ok.png"):
        find_and_click("message-ok.png")
        print("close message")
        wait(0.5)

    # TODO: logout change account
    # TODO: login


    print("Rageborn finished.")


if __name__ == "__main__":
    main()
