import pyautogui
import sys
import numpy as np
import time
import os
from pathlib import Path
import win32gui
import win32con
import win32process
import psutil

# Safety: Move mouse to top-left to abort
pyautogui.FAILSAFE = True

# Program Settings
BASE_IMAGE_DIR = "images"
CONFIDENCE = 0.75  # Adjust if detection fails
TARGETING_HERO = "Maliken"

# Mouse/Keyboard Input Settings
pyautogui.PAUSE = 0.3

#
def find_jokevio_hwnds():
    pids = [
        p.pid for p in psutil.process_iter(["name"])
        if p.info["name"] and p.info["name"].lower() == "juvio.exe"
    ]

    hwnds = []

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid in pids:
            hwnds.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return hwnds


def set_window_topmost(hwnd, enable=True):
    flag = win32con.HWND_TOPMOST if enable else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(
        hwnd,
        flag,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    )

def wait_for_jokevio_window(timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        hwnds = find_jokevio_hwnds()
        if hwnds:
            return hwnds
        time.sleep(0.3)
    return []

def launch_focus_and_pin_jokevio():
    print("Launching Jokevio...")

    # 1️⃣ Launch via desktop icon
    find_and_click("app-icon.png", doubleClick=True)

    # 2️⃣ Wait for window
    print("Waiting for Jokevio window...")
    hwnds = wait_for_jokevio_window()
    if not hwnds:
        raise RuntimeError("Jokevio window not found")

    # 3️⃣ Focus + Always-on-top
    for hwnd in hwnds:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        set_window_topmost(hwnd, True)

    # Find the logo and click
    while True:
        if image_exists("startup-disclamer-logo.png"):
            find_and_click("startup-disclamer-logo.png")
            break
        wait(0.5)

def unpin_jokevio():
    hwnds = find_jokevio_hwnds()
    for hwnd in hwnds:
        set_window_topmost(hwnd, False)

#
def image_exists(image_rel_path, region=None, confidence=None):
    full_path = resource_path(os.path.join(BASE_IMAGE_DIR, image_rel_path))
    try:
        return pyautogui.locateOnScreen(
            full_path,
            confidence=confidence if confidence is not None else CONFIDENCE,
            region=region
        ) is not None
    except pyautogui.ImageNotFoundException:
        return False
    
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
        raise TimeoutError(f"{image_rel_path} did not appear")

def find_and_click(image_rel_path, timeout=10, click=True, doubleClick=False, rightClick=False):
    """
    Finds an image on screen and clicks it.
    """
    full_path = resource_path(os.path.join(BASE_IMAGE_DIR, image_rel_path))
    start_time = time.time()

    while time.time() - start_time < timeout:
        location = pyautogui.locateCenterOnScreen(
            full_path,
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

    print(f"[ERROR] Could not find {image_rel_path}")
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
            #print(f"[OK] One of {wait_image_rel_path} appeared") # DEBUG
            return True

        try:
            location = pyautogui.locateCenterOnScreen(
                full_click_path,
                confidence=CONFIDENCE,
                region=region
            )

            if location:
                pyautogui.doubleClick(location)
                print(f"Clicking {TARGETING_HERO} hero portraits from selection")
                wait(0.5)

        except pyautogui.ImageNotFoundException:
            pass

        time.sleep(click_interval)

    if throwWhenTimedout:
        raise TimeoutError(f"{wait_image_rel_path} did not appear in time")

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
    wait(2.5)

def startQueue():
    while True:
        if not image_exists("matchmaking-disabled.png"):
            break
        else:
            print("Matchmaking Disabled, waiting connection...")
            wait(1)
        wait(0.5)

    # Tune matchmaking bar
    pyautogui.moveTo(922, 614, duration=0.3)    
    pyautogui.click()
    wait(0.3)

    # Click queue button
    pyautogui.moveTo(937, 729, duration=0.3)
    wait(0.3)
    pyautogui.click()
    print("Queue started. Waiting to get a match..")

    last_click_time = time.time()
    while True:
        now = time.time()
        
        if now - last_click_time > 30:
            print("Still not getting a match, requeuing..")
            pyautogui.moveTo(937, 729, duration=0.3)
            wait(0.2)
            pyautogui.click() # Unqueue
            wait(0.5)
            pyautogui.click() # Requeue
            last_click_time = now
        wait(0.1)

        if image_exists("message-taken-too-long.png", None):
            wait(2)
            print("'Waiting taken too long' message showed!")
            find_and_click("message-ok.png")
            print("Message dismissed!")
        
        # successfully joined a match: FOC
        if image_exists("foc-role-info.png"):
            print("Match found! Mode: Forest of Cunt!")
            wait(0.5)
            break

        wait(2)

def pickingPhase():
    find_and_click("foc-role-info.png")
    print("Picking phase begin..")
    wait(3)
    
    if click_until_image_appears(f"heroes/{TARGETING_HERO}/picking-phase.png", [f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-legion.png",f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-hellbourne.png"], 60, 0.5) == True:
        print(f"{TARGETING_HERO} selected")
        wait(0.5)
        pyautogui.moveTo(968, 336, duration=0.3) # move off hover hero selection
        print("Waiting to rageborn")
        return True
    else:
        # TODO: Random is just fine?
        print(f"{TARGETING_HERO} banned! Exiting game..")
        return False

def ingame():
    # Configuration
    side="legion"

    # TODO: clean up until use case happened
    while True:
        if not wait_until_appears("abandon-match-message.png", 3, None, 1):
            break
        else:
            return # Quit this function

    # TODO: should reset the timer while others picked their hero, so unnecessary wait is voided.
    if wait_until_appears("ingame-top-left-menu.png", 150):
        print("I see fountain, I see grief! Rageborn started!")
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
    print("Bought a Hatcher cost 150!")
    wait(0.5)
    find_and_click("ingame-shop-hatcher-icon.png", 2, False, False, True)
    print("Bought a Hatcher cost 150!")
    wait(0.5)
    find_and_click("ingame-shop-hatcher-icon.png", 2, False, False, True)
    print("Bought a Hatcher cost 150!")
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
                pyautogui.moveTo(510, 787, duration=0.3)
                wait(0.5)
                pyautogui.hotkey("alt", "t")
                wait(0.5)
                pyautogui.click()
                wait(3.5)            
                pyautogui.moveTo(528, 768, duration=0.3)
                wait(0.5)
                pyautogui.rightClick()
                wait(0.5)
                pyautogui.click()

            case "hellbourne":
                print("Applying Hellbourne coordinate!")
                pyautogui.moveTo(528, 768, duration=0.3)            
                wait(0.5)
                pyautogui.hotkey("alt", "t")
                wait(0.5)
                pyautogui.click()
                wait(3.5)
                pyautogui.moveTo(510, 787, duration=0.3)
                wait(0.5)
                pyautogui.rightClick()
                wait(0.5)
                pyautogui.click()
    
        # TODO: spam taunt (need to calculate or know already ready tower)    
        # TODO: death recap or respawn time show then stop spam

        wait(3)
        print("Waiting to get kick by the team...")
        
        # TODO: threading for this section; see vote press No
        if image_exists("vote-no.png"):
            print("See RED vote button! Decline whatever shit it is..")
            wait(1)
            find_and_click("vote-no.png")

        if image_exists("vote-no-black.png"):
            print("See BLACK vote button! Decline whatever shit it is..")
            wait(1)
            find_and_click("vote-no-black.png")        

        if any_image_exists([
            "not-a-host-message.png",
            "cancelled-match-message.png",
            "game-has-ended-message.png",
            "lobby-misc-message.png",
            "kicked-message.png",
            "no-response-from-server.png"
        ]):
            break

#
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#
def main(username, password):
    print("Rageborn started...")

    try:
        #
        launch_focus_and_pin_jokevio()

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
    
    finally:
        unpin_jokevio()

if __name__ == "__main__":
    main()
