import pyautogui
import numpy as np
import time
import win32gui
import win32con
import win32process
import psutil
from utilities.loggerSetup import setup_logger
import threading
import utilities.constants as constant
from threads.ingame import vote_requester, lobby_message_check_requester
from utilities.common import interruptible_wait, interruptible_wait
from utilities.imagesUtilities import find_and_click, image_exists, any_image_exists, click_until_image_appears
from core.parameters import TARGETING_HERO
import core.state as state
from utilities.datasetLoader import load_dataset
import utilities.coordinateAccess as assetsLibrary

# Initialize Logger
logger = setup_logger()

# Safety: Move mouse to top-left to abort
pyautogui.FAILSAFE = True

# Mouse/Keyboard Input Settings
pyautogui.PAUSE = 0.3

# Load Dataset
COORDS = load_dataset("coordinates_1920x1080")
assetsLibrary.init(COORDS)

#
def validate_coords(coords):
    required = ["in_game", "matchmaking_panel", "picking_phase"]
    for key in required:
        if key not in coords:
            raise RuntimeError(f"Invalid dataset: missing {key}")

#
def start(username, password):
    #
    state.init_cycle_number()

    threads = [
        threading.Thread(name="VoteWatcher", target=vote_requester),
        threading.Thread(name="LobbyMessageWatcher", target=lobby_message_check_requester)
    ]

    for t in threads:
        t.start()

    try:
        # Validate Coordinate
        validate_coords(COORDS)

        #
        main(username, password)
    finally:
        logger.info("[MAIN] shutting down")
        state.STOP_EVENT.set()
        
        for t in threads:
            t.join()

#
def find_juvio_platform_hwnd():
    hwnds = []

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)
        if title and "juvio platform" in title.lower():
            hwnds.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return hwnds


def wait_for_juvio_platform(timeout=60):
    logger.info("[INFO] Waiting for Juvio Platform window...")

    start = time.time()
    while time.time() - start < timeout:
        hwnds = find_juvio_platform_hwnd()
        if hwnds:
            return hwnds[0]
        time.sleep(0.3)

    raise RuntimeError("Juvio Platform window not found")


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

def force_foreground_and_topmost(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
    except Exception as e:
        logger.warning(f"[WARN] Failed to foreground hwnd={hwnd}: {e}")

def launch_focus_and_pin_jokevio():

    # 1️⃣ Launch via desktop icon
    icon1 = assetsLibrary.get_app_icon()
    icon2 = assetsLibrary.get_app_icon_default()
    if find_and_click(icon1, doubleClick=True, region=constant.SCREEN_REGION):
        logger.info("[INFO] Launching game...")
    elif find_and_click(icon2, doubleClick=True, region=constant.SCREEN_REGION):        
        logger.info("[INFO] Launching game...")
    else:
        raise RuntimeError("Failed to click Juvio desktop icon")

    # Give launcher a moment to bootstrap
    interruptible_wait(2.0)

    # 2️⃣ Wait for REAL UI window (Juvio Platform)
    hwnd = wait_for_juvio_platform()
    logger.info(f"[INFO] Juvio Platform hwnd={hwnd}")

    # 3️⃣ Bring window to front & pin topmost
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
        logger.info("[INFO] Juvio Platform pinned topmost")
    except Exception as e:
        logger.warning(f"[WARN] Failed to pin Juvio Platform: {e}")

    # 4️⃣ Wait for login / disclaimer UI to be visible
    logger.info("[INFO] Waiting for game client to surface...")

    start = time.time()
    while True:
        # 🔁 Re-detect platform/game window (launcher may have exited)
        hwnds = find_juvio_platform_hwnd()
        if hwnds:
            hwnd = hwnds[0]
            force_foreground_and_topmost(hwnd)

        # 🔍 Now check UI
        if any_image_exists([
            "startup/startup-disclamer-logo.png",
            "startup/username-field.png"
        ], region=constant.SCREEN_REGION):
            logger.info("[INFO] Startup UI detected")
            break

        if time.time() - start > 90:
            raise RuntimeError("Startup UI not detected within timeout")

        interruptible_wait(0.5)

    # 5️⃣ Dismiss disclaimer if present
    if find_and_click("startup/startup-disclamer-logo.png", region=constant.SCREEN_REGION):
        logger.info("[INFO] Dismissing startup disclaimer")        
        interruptible_wait(0.5)

    logger.info("[INFO] Juvio Platform ready for login")


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
    interruptible_wait(3)

    while True:
        # do nothing until found username-field.png
        if find_and_click("startup/username-field.png"):
            # Click username field
            break
        
    type_text(username)

    # Click password field (reuse if same)
    pyautogui.press("tab")
    type_text(password, enter=True)
    start_time = time.time()
    timeout = 10

    while not state.STOP_EVENT.is_set():
        # ⛔ Timeout protection
        if time.time() - start_time > timeout:
            logger.warning("[LOGIN] Timeout waiting for login result")
            return False

        # ❌ Login failed
        if any_image_exists([
            "startup/startup-account-not-found.png",
            "startup/startup-invalid-password.png"
        ]):
            logger.warning("[LOGIN] Invalid account or password detected")
            return False

        # ✅ Login success (pick a reliable UI signal)
        if image_exists("play-button.png", region=constant.SCREEN_REGION):
            logger.info(f"[LOGIN] Successfully logged in as {username}")
            return True

        time.sleep(0.3)

    logger.warning("[LOGIN] Login aborted due to STOP_EVENT")
    return False

def prequeue():
    # Queue options
    while True:
        logger.info("[INFO] Looking for PLAY button...")
        if find_and_click("play-button.png", region=constant.SCREEN_REGION):            
            logger.info("[INFO] PLAY button clicked!")            
            break
        interruptible_wait(0.7)    

def startQueue():
    interruptible_wait(1.25)

    # Tune matchmaking bar
    x, y = assetsLibrary.get_matchmaking_tuner_coord()
    pyautogui.moveTo(x, y, duration=0.3)    
    pyautogui.click()
    interruptible_wait(0.3)

    while True:
        if not image_exists("matchmaking-disabled.png", region=constant.MATCHMAKING_PANEL_REGION):
            break
        else:
            logger.info("[INFO] Matchmaking Disabled, waiting connection...")
            interruptible_wait(1)
        interruptible_wait(0.5)

    # Click queue button
    x, y = assetsLibrary.get_queue_button_coord()
    pyautogui.moveTo(x, y, duration=0.3)
    interruptible_wait(0.3)
    pyautogui.click()
    logger.info("[INFO] Queue started. Waiting to get a match..")

    last_click_time = time.time()
    while True:
        now = time.time()

        if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/failed-to-fetch-mmr-message.png", region=constant.LOBBY_MESSAGE_REGION):
            logger.info("[INFO] 'Failed to fetch mmr' message showed!")
            if find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
                logger.info("[INFO] Message dismissed!")
            else:
                logger.info("[ERROR] Unable to locate OK button.")

        if not image_exists("waiting-for-players.png", region=constant.MATCHMAKING_PANEL_REGION):
        
            if now - last_click_time > 95:
                logger.info("[INFO] Performing requeuing, due to timeout")
                pyautogui.moveTo(x, y, duration=0.3)
                interruptible_wait(1)
                pyautogui.click() # Unqueue
                logger.info("[INFO] Stop queuing")
                interruptible_wait(1)
                pyautogui.click() # Requeue
                logger.info("[INFO] Start queuing")
                last_click_time = now
        else:            
            # Reset timer (Requeue)
            last_click_time = time.time()
            now = time.time()

        interruptible_wait(0.1)

        if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/taken-too-long-message.png", region=constant.LOBBY_MESSAGE_REGION):
            interruptible_wait(2)
            logger.info("[INFO] 'Waiting taken too long' message showed!")
            if find_and_click("message-ok.png"):
                logger.info("[INFO] Message dismissed!")
            else:
                logger.info("[ERROR] Unable to locate OK button.")
        
        # successfully joined a match: FOC
        if any_image_exists([
            "foc-role-info.png",
            "choose-a-hero-button.png"
        ]):
            logger.info("[INFO] Match found! Mode: Forest of Cunt!")
            state.INGAME_STATE.setCurrentMap(constant.MAP_FOC)
            interruptible_wait(0.5)
            break

        interruptible_wait(2)

def pickingPhase():
    match state.INGAME_STATE.getCurrentMap():
        case constant.MAP_FOC:

            # TODO: Support others mode
            x,y = assetsLibrary.get_picking_dismiss_safezone_coord()
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.click() # dismiss foc role information
            logger.info("[INFO] FOC Role information dismissed..")
            logger.info("[INFO] Picking phase begin..")
            interruptible_wait(0.5)
            
            # TODO: Alternative hero selection
            if click_until_image_appears(f"heroes/{TARGETING_HERO}/picking-phase.png", [f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-legion.png",f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-hellbourne.png"], 60, 0.5) == True:
                logger.info(f"[INFO] {TARGETING_HERO} selected")
                interruptible_wait(0.5)        
                pyautogui.moveTo(x, y, duration=0.3) # move off hover hero selection
                logger.info("[INFO] Waiting to rageborn")
            else:
                # TODO: Random is just fine?
                logger.info(f"[INFO] {TARGETING_HERO} banned!")
                logger.info("[INFO] Waiting to get random hero.")

    while True:
        if image_exists("ingame-top-left-menu.png", region=constant.SCREEN_REGION):
            logger.info("[INFO] I see fountain, I see grief!")
            logger.info("[INFO] Rageborn begin!")
            interruptible_wait(1.5)
            return True
        
        elif image_exists("play-button.png", region=constant.SCREEN_REGION):
            # Back to lobby
            logger.info("[INFO] Match aborted!")
            return False
        
        interruptible_wait(2)

# TODO: Incomplete code
def define_team():
    # check team team 
    pyautogui.keyDown("x")
    if any_image_exists([
        "foc-fountain-legion.png",
        "scoreboard-legion.png"
        ]):
        team = constant.TEAM_LEGION
    else:
        team = constant.TEAM_HELLBOURNE
    
    state.INGAME_STATE.setCurrentTeam(team)
    logger.info(f"[INFO] We are on {team} team!")
    interruptible_wait(2)
    pyautogui.keyUp("x")
    interruptible_wait(0.5)

# FOC
def do_lane_push_step(team):
    # Will go random lane
    map = state.INGAME_STATE.getCurrentMap()
    lane_number = state.get_cycle_number()

    LANE_BY_NUMBER = {
        1: constant.LANE_TOP,
        2: constant.LANE_MID,
        3: constant.LANE_BOT,
    }

    lane = LANE_BY_NUMBER[lane_number]

    x1, y1 = assetsLibrary.get_friendly_tower_coord(map, team, lane, 3)
    x2, y2 = assetsLibrary.get_enemy_base_coord(map, team)

    pyautogui.moveTo(x1, y1, duration=0.3)
    pyautogui.hotkey("alt", "t")
    pyautogui.click()
    pyautogui.moveTo(x2, y2, duration=0.3)
    pyautogui.rightClick()

# FOC
def do_foc_stuff():
    # check team team 
    pyautogui.keyDown("x")
    if any_image_exists([
        "foc-fountain-legion.png",
        "scoreboard-legion.png"
        ]):
        team = constant.TEAM_LEGION
    else:
        team = constant.TEAM_HELLBOURNE
    
    state.INGAME_STATE.setCurrentTeam(team)
    logger.info(f"[INFO] We are on {team} team!")
    interruptible_wait(2)
    pyautogui.keyUp("x")
    interruptible_wait(0.5)

    #
    bought = False
    pyautogui.keyDown("c") # center hero

    #
    matchTimedout = 500 # after 500 seconds from now will automatic leave the game    
    start_time = time.monotonic()
    while not state.STOP_EVENT.is_set():
        elapsed = time.monotonic() - start_time

        if not state.STOP_EVENT.is_set() and state.SCAN_VOTE_EVENT.is_set():
            state.SCAN_VOTE_EVENT.clear()

            if find_and_click("vote-no.png", region=constant.VOTE_REGION):
                logger.info("[INFO] Kick Vote detected — declining")

            if find_and_click("vote-no-black.png", region=constant.VOTE_REGION):
                logger.info("[INFO] Remake Vote detected — declining")
        
        if not state.STOP_EVENT.is_set() and not bought:
            # open ingame shop
            pyautogui.press("b")
            logger.info("[INFO] Opening ingame shop")
            interruptible_wait(0.5)
            
            # locate to enchantment icon
            logger.info("[INFO] Finding Jade Spire from enchantment tab")
            if find_and_click("ingame-shop-enchantment-icon.png", region=constant.INGAME_SHOP_REGION):
                time.sleep(0.5)
                # find Jade Spire recipe
                if find_and_click("ingame-shop-jade-spire-icon.png", rightClick=True, region=constant.INGAME_SHOP_REGION):                    
                    time.sleep(0.5)
                    if find_and_click("ingame-shop-jade-spire-icon.png", region=constant.INGAME_SHOP_REGION):
                        for _ in range(4):
                            if find_and_click(
                                "ingame-shop-jade-spire-recipe-owned-icon.png",
                                rightClick=True,
                                region=constant.INGAME_SHOP_REGION
                            ):
                                logger.info("[INFO] Bought a Jade Spire recipe cost 100g!")
                            else:
                                logger.info("[INFO] Jade Spire already missing / no gold / UI changed")
                            time.sleep(0.3)

            interruptible_wait(0.3)
            # close ingame shop
            pyautogui.press("esc")
            logger.info("[INFO] Ingame shop closed")
            bought = True
            logger.info("[INFO] Waiting to get kick by the team...")
            interruptible_wait(0.5)
        
        if not state.STOP_EVENT.is_set():
            # mouse cursor to team mid tower
            # alt+t and click to team mid tower
            # mouse cursor to enemy mid tower
            # right click to enemy mid tower

            do_lane_push_step(team)
            
            # TODO: spam taunt (need to calculate or know already ready tower)    
            # TODO: death recap or respawn time show then stop spam

        if not state.STOP_EVENT.is_set() and state.SCAN_LOBBY_MESSAGE_EVENT.is_set():
            state.SCAN_LOBBY_MESSAGE_EVENT.clear()

            if check_lobby_message():
                pyautogui.keyUp("c") # stop spamming                
                state.STOP_EVENT.set()
                break
        
        if elapsed >= matchTimedout:
            logger.info(f"[TIMEOUT] {matchTimedout} seconds reached. Stopping.")
            state.STOP_EVENT.set()
            break

        interruptible_wait(0.03)

# TODO: Incomplete code
# Midwar
def do_midwar_stuff():
    # check team team 
    pyautogui.keyDown("x")
    if any_image_exists([
        "foc-fountain-legion.png",
        "scoreboard-legion.png"
        ]):
        team = constant.TEAM_LEGION
    else:
        team = constant.TEAM_HELLBOURNE
    
    state.INGAME_STATE.setCurrentTeam(team)
    logger.info(f"[INFO] We are on {team} team!")
    interruptible_wait(2)
    pyautogui.keyUp("x")
    interruptible_wait(0.5)

def check_lobby_message():
    return any_image_exists([
        f"{constant.DIALOG_MESSAGE_DIR}/not-a-host-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/cancelled-match-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/game-has-ended-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/lobby-misc-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/kicked-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/no-response-from-server-message.png"
    ], region=constant.LOBBY_MESSAGE_REGION)        

def ingame(): 
    #
    logger.info("[INFO] HERE COMES THE TROLL BEGIN")

    match state.INGAME_STATE.getCurrentMap():
        case constant.MAP_FOC:
            do_foc_stuff()

        case constant.MAP_MIDWAR:
            do_midwar_stuff()

#
def main(username, password):
    logger.info("[INFO] Rageborn boot up...")

    try:
        #
        launch_focus_and_pin_jokevio()

        # Account Login manually
        if account_Login(username, password):

            while not state.STOP_EVENT.is_set():
                #
                prequeue()

                #
                startQueue()

                logger.info("[DEBUG] startQueue finished, entering pickingPhase")
                
                #
                result = pickingPhase()
                logger.info(f"[DEBUG] pickingPhase returned: {result}")                

                if not result:

                    # Just in case message pops
                    if any_image_exists([
                        f"{constant.DIALOG_MESSAGE_DIR}/not-a-host-message.png",
                        f"{constant.DIALOG_MESSAGE_DIR}/cancelled-match-message.png",
                        f"{constant.DIALOG_MESSAGE_DIR}/game-has-ended-message.png",
                        f"{constant.DIALOG_MESSAGE_DIR}/lobby-misc-message.png",
                        f"{constant.DIALOG_MESSAGE_DIR}/kicked-message.png",
                        f"{constant.DIALOG_MESSAGE_DIR}/no-response-from-server-message.png"
                    ], region=constant.LOBBY_MESSAGE_REGION):
                        location = image_exists("message-ok.png", region=constant.LOBBY_MESSAGE_REGION)
                        if location == True:
                            pyautogui.click(location)
                            logger.info("[INFO] Message box closed!")

                    logger.warning("[QUEUE] Match aborted, restarting queue")
                    continue

                ingame()

        logger.info("[INFO] Rageborn shutting down...")
    
    finally:
        unpin_jokevio() 
