import pyautogui
import numpy as np
import time
import win32gui
import win32con
import win32process
import psutil
from utilities.loggerSetup import setup_logger
import threading
from utilities.constants import SCREEN_REGION, MATCHMAKING_PANEL_REGION, LOBBY_MESSAGE_REGION, INGAME_SHOP_REGION, DIALOG_MESSAGE_DIR, VOTE_REGION
from threads.ingame import vote_requester, lobby_message_check_requester
from utilities.common import wait, interruptible_wait
from utilities.imagesUtilities import find_and_click, image_exists, any_image_exists, click_until_image_appears
from core.parameters import TARGETING_HERO
import core.state as state

# Initialize Logger
logger = setup_logger()

# Safety: Move mouse to top-left to abort
pyautogui.FAILSAFE = True

# Mouse/Keyboard Input Settings
pyautogui.PAUSE = 0.3

#
def start(username, password):
    threads = [
        threading.Thread(name="VoteWatcher", target=vote_requester),
        threading.Thread(name="LobbyMessageWatcher", target=lobby_message_check_requester)
    ]

    for t in threads:
        t.start()

    try:
        main(username, password)
    finally:
        logger.info("[MAIN] shutting down")
        state.STOP_EVENT.set()

        # ⏳ wait for threads to exit cleanly
        for t in threads:
            t.join()

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
    logger.info(f"[INFO] Launching game...")

    # 1️⃣ Launch via desktop icon
    find_and_click("app-icon.png", doubleClick=True, region=SCREEN_REGION)

    # 2️⃣ Wait for window
    logger.info("[INFO] Waiting for Jokevio window to be detected...")
    hwnds = wait_for_jokevio_window()
    if not hwnds:
        logger.info("[APP_ERROR] Jokevio window couldn't be found!")
        raise RuntimeError("Jokevio window not found")

    # 3️⃣ Focus + Always-on-top
    for hwnd in hwnds:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        set_window_topmost(hwnd, True)

    # Find the logo and click
    while True:
        if image_exists("startup/startup-disclamer-logo.png"):
            find_and_click("startup/startup-disclamer-logo.png")
            break
        wait(0.5)

def unpin_jokevio():
    hwnds = find_jokevio_hwnds()
    for hwnd in hwnds:
        set_window_topmost(hwnd, False)

#
def type_text(text, enter=False):
    pyautogui.write(text, interval=0.05)
    if enter:
        pyautogui.press("enter")


#
def account_Login(username, password):
    wait(3)

    while True:
        # do nothing until found username-field.png
        if find_and_click("startup/username-field.png"):
            # Click username field
            break
        
    type_text(username)

    # Click password field (reuse if same)
    pyautogui.press("tab")
    type_text(password, enter=True)
    logger.info("[INFO] Waiting account to login...")
    wait(3)

    # 
    if any_image_exists([
        "startup/startup-account-not-found.png",
        "startup/startup-invalid-password.png"
    ]):
        logger.info("[INFO] Invalid account / password detected.")
        logger.info("[INFO] Aborting...")
        return False
    else:
        logger.info(f"[INFO] Login as {username}")
        return True

def prequeue():
    # Queue options
    while True:
        logger.info("[INFO] Looking for PLAY button...")
        if image_exists("play-button.png", region=SCREEN_REGION):
            find_and_click("play-button.png", region=SCREEN_REGION)
            logger.info("[INFP] PLAY button clicked!")
            wait(2.5)
            break
        wait(0.7)    

def startQueue():
    while True:
        if not image_exists("matchmaking-disabled.png", region=MATCHMAKING_PANEL_REGION):
            break
        else:
            logger.info("[INFO] Matchmaking Disabled, waiting connection...")
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
    logger.info("[INFO] Queue started. Waiting to get a match..")

    last_click_time = time.time()
    while True:
        now = time.time()
        
        if now - last_click_time > 60:
            logger.info("[INFO] Performing requeuing, due to timeout")
            pyautogui.moveTo(937, 729, duration=0.3)
            wait(0.5)
            pyautogui.click() # Unqueue
            logger.info("[INFO] Stop queuing")
            wait(0.7)
            pyautogui.click() # Requeue
            logger.info("[INFO] Start queuing")
            last_click_time = now
        wait(0.1)

        if image_exists(f"{DIALOG_MESSAGE_DIR}/taken-too-long-message.png", region=LOBBY_MESSAGE_REGION):
            wait(2)
            logger.info("[INFO] 'Waiting taken too long' message showed!")
            find_and_click("message-ok.png")
            logger.info("[INFO] Message dismissed!")
        
        # successfully joined a match: FOC
        if any_image_exists([
            "foc-role-info.png",
            "choose-a-hero-button.png"
        ]):
            logger.info("[INFO] Match found! Mode: Forest of Cunt!")
            wait(0.5)
            break

        wait(2)

def pickingPhase():
    find_and_click("foc-role-info.png")
    logger.info("[INFO] Picking phase begin..")
    wait(3)
    
    # TODO: Alternative hero selection
    if click_until_image_appears(f"heroes/{TARGETING_HERO}/picking-phase.png", [f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-legion.png",f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-hellbourne.png"], 60, 0.5) == True:
        logger.info(f"[INFO] {TARGETING_HERO} selected")
        wait(0.5)
        pyautogui.moveTo(968, 336, duration=0.3) # move off hover hero selection
        logger.info("[INFO] Waiting to rageborn")
    else:
        # TODO: Random is just fine?
        logger.info(f"[INFO] {TARGETING_HERO} banned!")
        logger.info("[INFO] Waiting to get random hero.")

    while True:
        if image_exists("ingame-top-left-menu.png", region=SCREEN_REGION):
            logger.info("[INFO] I see fountain, I see grief! Rageborn started!")
            wait(1.5)
            return True
        
        elif image_exists("play-button.png", region=SCREEN_REGION):
            # Back to lobby
            logger.info("[INFO] Match aborted!")
            return False
        
        wait(2)

def ingame():
    # Configuration
    side="legion"    

    logger.info("[INFO] HERE COMES THE TROLL")

    # check team side 
    pyautogui.keyDown("x")
    if image_exists("scoreboard-legion.png"):
        logger.info("[INFO] We are on Legion side!")
        side="legion"
    else:
        logger.info("[INFO] We are on Hellbourne side!")
        side="hellbourne"
    wait(2)
    pyautogui.keyUp("x")
    wait(0.5)

    bought = False
    pyautogui.keyDown("c") # center hero
    while not state.STOP_EVENT.is_set():        

        if not state.STOP_EVENT.is_set() and state.SCAN_VOTE_EVENT.is_set():
            state.SCAN_VOTE_EVENT.clear()

            if image_exists("vote-no.png", region=VOTE_REGION):
                logger.info("[INFO] Kick Vote detected — declining")
                find_and_click("vote-no.png", region=VOTE_REGION)

            if image_exists("vote-no-black.png", region=VOTE_REGION):
                logger.info("[INFO] Remake Vote detected — declining")
                find_and_click("vote-no-black.png", region=VOTE_REGION)
        
        if not state.STOP_EVENT.is_set() and not bought:
            # open ingame shop
            pyautogui.press("b")
            logger.info("[INFO] Opening ingame shop")
            wait(0.5)
            # locate to initiation icon
            logger.info("[INFO] Finding Hatcher from initiation tab")
            find_and_click("ingame-shop-initiation-icon.png", region=INGAME_SHOP_REGION)
            wait(0.3)
            # find hatcher
            # right click hatcher
            find_and_click("ingame-shop-hatcher-icon.png", rightClick=True, region=INGAME_SHOP_REGION)
            logger.info("[INFO] Bought a Hatcher cost 150g!")
            find_and_click("ingame-shop-hatcher-icon.png", rightClick=True, region=INGAME_SHOP_REGION)
            logger.info("[INFO] Bought a Hatcher cost 150g!")
            find_and_click("ingame-shop-hatcher-icon.png", rightClick=True, region=INGAME_SHOP_REGION)
            logger.info("[INFO] Bought a Hatcher cost 150g!")
            wait(0.3)
            # close ingame shop
            pyautogui.press("esc")
            logger.info("[INFO] Ingame shop closed")
            bought = True
            logger.info("[INFO] Waiting to get kick by the team...")
            wait(0.5)
        
        if not state.STOP_EVENT.is_set():
            # mouse cursor to team mid tower
            # alt+t and click to team mid tower
            # mouse cursor to enemy mid tower
            # right click to enemy mid tower
            match side:
                case "legion":                
                    pyautogui.moveTo(510, 787, duration=0.3) # friendly tower
                    pyautogui.hotkey("alt", "t")
                    pyautogui.click()
                    pyautogui.moveTo(574, 721, duration=0.3) # enemy base
                    pyautogui.rightClick()
                    pyautogui.click()

                case "hellbourne":                
                    pyautogui.moveTo(528, 768, duration=0.3) # friendly tower
                    pyautogui.hotkey("alt", "t")
                    pyautogui.click()
                    pyautogui.moveTo(465, 837, duration=0.3) # enemy base
                    pyautogui.rightClick()
                    pyautogui.click()
            
            # TODO: spam taunt (need to calculate or know already ready tower)    
            # TODO: death recap or respawn time show then stop spam

        if not state.STOP_EVENT.is_set() and state.SCAN_LOBBY_MESSAGE_EVENT.is_set():
            state.SCAN_LOBBY_MESSAGE_EVENT.clear()

            if any_image_exists([
                f"{DIALOG_MESSAGE_DIR}/not-a-host-message.png",
                f"{DIALOG_MESSAGE_DIR}/cancelled-match-message.png",
                f"{DIALOG_MESSAGE_DIR}/game-has-ended-message.png",
                f"{DIALOG_MESSAGE_DIR}/lobby-misc-message.png",
                f"{DIALOG_MESSAGE_DIR}/kicked-message.png",
                f"{DIALOG_MESSAGE_DIR}/no-response-from-server-message.png"
            ], region=LOBBY_MESSAGE_REGION):
                pyautogui.keyUp("c") # stop spamming
                state.STOP_EVENT.set()
                break

        wait(0.03)

#
def main(username, password):
    logger.info("[INFO] Rageborn boot up...")

    try:
        #
        launch_focus_and_pin_jokevio()

        # Account Login manually
        if account_Login(username, password):
            #
            prequeue()

            #
            startQueue()    
            
            #    
            if pickingPhase() == True:
                ingame()
            else:
                # if match aborted
                return
            
            #
            logger.info("[INFO] We are in the game lobby!")
            wait(0.5)
            location = image_exists("message-ok.png", region=LOBBY_MESSAGE_REGION)
            if location == True:
                pyautogui.click(location)
                logger.info("[INFO] Message box closed!")
                wait(0.5)

            # TODO: logout change account
            # TODO: login

        logger.info("[INFO] Rageborn shutting down...")
    
    finally:
        unpin_jokevio() 
