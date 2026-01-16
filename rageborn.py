import pyautogui
import numpy as np
import time
import win32api
import win32gui
import win32con
import win32process
import psutil
from threads.hwnd_watchdog import start_hwnd_watchdog
from utilities.appUtilities import is_fullscreen
from utilities.loggerSetup import setup_logger
import threading
import utilities.constants as constant
from threads.ingame import vote_requester, lobby_message_check_requester
from utilities.common import interruptible_wait, interruptible_wait
from utilities.imagesUtilities import find_and_click, image_exists, any_image_exists, image_exists_in_any_region
from core.parameters import TARGETING_HERO
import core.state as state
from utilities.datasetLoader import load_dataset
import utilities.coordinateAccess as assetsLibrary
import keyboard
import random
import os
import subprocess
from utilities.common import resource_path

# Initialize Logger
logger = setup_logger()

# Safety: Move mouse to top-left to abort
pyautogui.FAILSAFE = True

# Mouse/Keyboard Input Settings
pyautogui.PAUSE = 0.3

# Load Dataset
COORDS = load_dataset("coordinates_1920x1080")
assetsLibrary.init(COORDS)

# ================= EMERGENCY STOP =================
def emergency_stop():
    logger.critical("[EMERGENCY] F11 pressed! HARD STOP triggered.")
    os._exit(0)   # 🔥 immediate hard kill


keyboard.add_hotkey("F11", emergency_stop)
# =================================================

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
        stop_powershell()
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


def run_powershell_async():
    threading.Thread(
        target=run_powershell,
        name="PowerShellPriorityThread",
        daemon=True
    ).start()


def run_powershell():
    global ps_priority_proc
    subprocess.run([
        "powershell",
        "-NoProfile",
        "-Command",
        "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force"
    ],
    creationflags=subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL)
    interruptible_wait(0.5)
    script_path = resource_path("scripts/set_game_priority.ps1")
    ps_priority_proc = subprocess.Popen([
        "powershell",
        "-NoProfile",
        "-File", script_path
    ],
    creationflags=subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL)


def stop_powershell():
    global ps_priority_proc

    if ps_priority_proc and ps_priority_proc.poll() is None:
        ps_priority_proc.terminate()
        ps_priority_proc = None


def set_game_high_priority(
    exe_name="juvio.exe",
    duration=10,
    interval=0.5
):
    """
    Force HIGH priority on the game process for a short window
    to survive launcher resets.
    """

    logger.info(f"[PRIORITY] Enforcing HIGH priority for {exe_name}")

    end_time = time.time() + duration

    while time.time() < end_time:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == exe_name.lower():
                    if proc.nice() != psutil.HIGH_PRIORITY_CLASS:
                        proc.nice(psutil.HIGH_PRIORITY_CLASS)
                        logger.info(
                            f"[PRIORITY] {exe_name} PID={proc.pid} set to HIGH"
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        time.sleep(interval)


def pin_jokevio():

    # 1 Launch .exe from ragebirth

    # Give launcher a moment to bootstrap
    interruptible_wait(2.0 if not state.SLOWER_PC_MODE else 4.0)

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
    while not state.STOP_EVENT.is_set():
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

        interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 0.7)

    # todo: fullscreen detection; unknown stupid game issue; investigation required
    #if is_fullscreen(hwnd):
    #    logger.info("[INFO] Juvio Platform is in fullscreen mode")
    #    state.STOP_EVENT.set()

    # Ensure powershell priority script is running
    run_powershell_async()
    start_hwnd_watchdog(        # start watchdog thread
        hwnd=hwnd,
        stop_event=state.STOP_EVENT,
        crash_event=state.CRASH_EVENT
    )

    # 5️⃣ Dismiss disclaimer if present
    if find_and_click("startup/startup-disclamer-logo.png", region=constant.SCREEN_REGION):
        logger.info("[INFO] Dismissing startup disclaimer")        
        interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)

    logger.info("[INFO] Juvio Platform ready for login")


def unpin_jokevio():
    hwnds = find_jokevio_hwnds()
    for hwnd in hwnds:
        set_window_topmost(hwnd, False)

#
def type_text(text, enter=False):
    pyautogui.write(text, interval=0.05)
    time.sleep(0.7)
    if enter:
        pyautogui.press("enter")

#
def account_Login(username, password):
    interruptible_wait(3)

    while not state.STOP_EVENT.is_set():
        # do nothing until found username-field.png
        if find_and_click("startup/username-field.png"):
            # Click username field
            break
        
    type_text(username)

    # Click password field (reuse if same)
    pyautogui.press("tab")
    type_text(password, enter=True)
    start_time = time.time()
    timeout = 10 if not state.SLOWER_PC_MODE else 15

    while not state.STOP_EVENT.is_set():
        # ⛔ Timeout protection
        if time.time() - start_time > timeout:
            logger.warning("[LOGIN] Timeout waiting for login result")
            return False

        # ❌ Login failed
        #if any_image_exists([
        #    "startup/startup-account-not-found.png",
        #    "startup/startup-invalid-password.png"
        #]):
        #    logger.warning("[LOGIN] Invalid account or password detected")
        #    return False

        # ✅ Login success (pick a reliable UI signal)
        if any_image_exists([
            "play-button.png", "play-button-christmas.png"
            ], region=constant.SCREEN_REGION):
            logger.info(f"[LOGIN] Successfully logged in as {username}")
            state.INGAME_STATE.setUsername(username)
            return True

        time.sleep(0.3)

    logger.warning("[LOGIN] Login aborted due to STOP_EVENT")
    return False

def prequeue():
    # Queue options
    while not state.STOP_EVENT.is_set():
        logger.info("[INFO] Looking for PLAY button...")
        if find_and_click("play-button.png", region=constant.SCREEN_REGION):            
            logger.info("[INFO] PLAY button clicked!")            
            break

        if find_and_click("play-button-christmas.png", region=constant.SCREEN_REGION):            
            logger.info("[INFO] PLAY button clicked!")            
            break

        interruptible_wait(0.7)    

def startQueue():
    interruptible_wait(1.25)

    # Tune matchmaking bar
    x, y = assetsLibrary.get_matchmaking_tuner_coord()
    pyautogui.moveTo(x, y, duration=0.3)    
    pyautogui.click()
    interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)

    while not state.STOP_EVENT.is_set():
        if not image_exists("matchmaking-disabled.png", region=constant.MATCHMAKING_PANEL_REGION):
            break
        else:
            logger.info("[INFO] Matchmaking Disabled, waiting connection...")
            interruptible_wait(1)
        interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)

    # Click queue button
    x, y = assetsLibrary.get_queue_button_coord()
    pyautogui.moveTo(x, y, duration=0.3)
    interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
    pyautogui.click()    
    interruptible_wait(1.5 if not state.SLOWER_PC_MODE else 3)
    logger.info("[INFO] Queue started. Waiting to get a match..")

    while not state.STOP_EVENT.is_set():

        # Requeue
        if any_image_exists(["play-button.png", "play-button-christmas.png"], region=constant.SCREEN_REGION):
            logger.info("[INFO] Still seeing PLAY button.. Re-queueing..")
            pyautogui.moveTo(x, y, duration=0.3)
            interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
            pyautogui.click()

        if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/failed-to-fetch-mmr-message.png", region=constant.LOBBY_MESSAGE_REGION):
            logger.info("[INFO] 'Failed to fetch mmr' message showed!")
            if find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
                logger.info("[INFO] Message dismissed!")
                pyautogui.moveTo(x, y, duration=0.3)
                interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
                pyautogui.click()
            else:
                logger.info("[ERROR] Unable to locate OK button.")

        if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/taken-too-long-message.png", region=constant.LOBBY_MESSAGE_REGION):
            interruptible_wait(2 if not state.SLOWER_PC_MODE else 2.5)
            logger.info("[INFO] 'Waiting taken too long' message showed!")
            if find_and_click("message-ok.png"):
                logger.info("[INFO] Message dismissed!")
            else:
                logger.info("[ERROR] Unable to locate OK button.")

        if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/not-a-host-message.png", region=constant.LOBBY_MESSAGE_REGION):
            interruptible_wait(2 if not state.SLOWER_PC_MODE else 2.5)
            logger.info("[INFO] 'Not a host' message showed!")
            if find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
                logger.info("[INFO] Message dismissed!")
            else:
                logger.info("[ERROR] Unable to locate OK button.")

        if image_exists("queue-cooldown.png", region=constant.SCREEN_REGION):
            return False
        
        # successfully joined a match: FOC
        if any_image_exists([
            "foc-role-info.png",
            "choose-a-hero-button.png"
        ]):
            logger.info("[INFO] Match found! Mode: Forest of Cunt!")
            state.INGAME_STATE.setCurrentMap(constant.MAP_FOC)
            interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)
            return True

        interruptible_wait(1 if not state.SLOWER_PC_MODE else 1.5)



def getTeam():
    interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 3)
    team = constant.TEAM_LEGION # Default

    match state.INGAME_STATE.getCurrentMap():
        case constant.MAP_FOC:
            # click minimap
            pyautogui.click(511,792)
            interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 4)
            if any_image_exists([
                "foc-mid-tower-legion.png"
                ]):
                team = constant.TEAM_LEGION
            else:
                team = constant.TEAM_HELLBOURNE
    
    state.INGAME_STATE.setCurrentTeam(team)
    logger.info(f"[INFO] We are on {team} team!")
    interruptible_wait(1 if not state.SLOWER_PC_MODE else 2)
    pyautogui.press("c")
    interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)
    return team

def enterChat(text):
    pyautogui.moveTo(921, 831)
    pyautogui.click()
    type_text(text=text, enter=True)

def pickingPhaseChat():
    chatChance = 0.5 if not state.SLOWER_PC_MODE else 0.3 
    if random.random() < chatChance:
        randomString = [
            "ezwin",
            "got me got win game",
            "glhf!!",
            "hi guys",
            "hello team",
            "yo",
            "show pick",
            "show pick please",
            "go pick"
        ]
        text = random.choice(randomString)
        enterChat(text)


def continuePickingPhaseChat():
    chatChance = 0.375 if not state.SLOWER_PC_MODE else 0.2
    if random.random() < chatChance:
        randomString = [
            "?",
            "??",
            "what",
            "?"
        ]
        text = random.choice(randomString)
        enterChat(text)
        interruptible_wait(round(random.uniform(5, 11), 2))

        chatChance = 0.35 if not state.SLOWER_PC_MODE else 0.2
        if random.random() < chatChance:
            role = state.INGAME_STATE.getFocRole()
            randomString = [
                "you ok?",
                "you sure?",
                "what you talking about",
                f"did i made a mistake on picking a hero from {role}?"
            ]
            text = random.choice(randomString)
            enterChat(text)
            interruptible_wait(round(random.uniform(5, 11), 2))

            chatChance = 0.3 if not state.SLOWER_PC_MODE else 0.15
            if random.random() < chatChance:
                randomString = [
                    "are you out of your mind?",
                    "bot your mum",
                    "your mum is the bot, why dont you kick her? stupid idiot",
                    "new player not welcoming to play this game?"
                ]
                text = random.choice(randomString)
                enterChat(text)


def pickingPhase():
    match state.INGAME_STATE.getCurrentMap():
        case constant.MAP_FOC:

            logger.info("[INFO] Detecting role..")

            # TODO: detect role that appear onscreen
            carryRole = assetsLibrary.get_foc_role_information(constant.FOC_ROLE_CARRY)
            softSupportRole = assetsLibrary.get_foc_role_information(constant.FOC_ROLE_SOFT_SUPPORT)
            hardSupportRole = assetsLibrary.get_foc_role_information(constant.FOC_ROLE_SOFT_SUPPORT)
            offlaneRole = assetsLibrary.get_foc_role_information(constant.FOC_ROLE_OFFLANE)
            midRole = assetsLibrary.get_foc_role_information(constant.FOC_ROLE_MID)

            timeout = 5 if not state.SLOWER_PC_MODE else 10
            role = constant.FOC_ROLE_HARD_SUPPORT # default role
            roleCheckStart = time.time()
            while not state.STOP_EVENT.is_set():
                now = time.time()
                if image_exists(carryRole):
                    logger.info("[INFO] Assignated Role: Carry")
                    role = constant.FOC_ROLE_CARRY
                    break
                elif image_exists(softSupportRole):
                    logger.info("[INFO] Assignated Role: Soft Support")
                    role = constant.FOC_ROLE_SOFT_SUPPORT
                    break
                elif image_exists(hardSupportRole):
                    logger.info("[INFO] Assignated Role: Hard Support")
                    role = constant.FOC_ROLE_HARD_SUPPORT
                    break
                elif image_exists(offlaneRole):
                    logger.info("[INFO] Assignated Role: Offlane")
                    role = constant.FOC_ROLE_OFFLANE
                    break
                elif image_exists(midRole):
                    logger.info("[INFO] Assignated Role: Mid")
                    role = constant.FOC_ROLE_MID
                    break
                elif now - roleCheckStart > timeout:
                    logger.info(f"[INFO] Unable to detect role.. use {role}")
                    break

            state.INGAME_STATE.setFocRole(role=role)

            randomWaitingChance = 0.6
            if random.random() < randomWaitingChance:
                interruptible_wait(round(random.uniform(5, 10), 2))

            notafkChance = 0.93
            if random.random() < notafkChance: 
                x,y = assetsLibrary.get_picking_dismiss_safezone_coord()
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.click() # dismiss foc role information
                logger.info("[INFO] FOC Role information dismissed..")
                logger.info("[INFO] Picking phase begin..")
                interruptible_wait(round(random.uniform(0.5, 1), 2))            

                hero, hx1, hy1 = assetsLibrary.get_role_heroes_coord(role)
                logger.info(f"[INFO] Selecting {hero}")
                pyautogui.moveTo(hx1, hy1, duration=0.3)
                interruptible_wait(round(random.uniform(0.4, 1), 2))

                shuffleSelectionChance = 0.3 if not state.SLOWER_PC_MODE else 0.2
                if random.random() < shuffleSelectionChance:
                    number = random.randint(3, 6)
                    for i in range(number):
                        hero, hx, hy = assetsLibrary.get_role_heroes_coord(role)
                        #logger.info(f"[INFO] Showcasing shuffle hero")
                        pyautogui.moveTo(hx, hy, duration=0.3)
                        pyautogui.click()
                        interruptible_wait(round(random.uniform(0.7, 1.5), 2))
                    pyautogui.moveTo(hx1, hy1, duration=0.3)

                shadowpickChance = 0.65
                if random.random() < shadowpickChance:
                    pyautogui.click()
                    interruptible_wait(round(random.uniform(4, 7), 2))                    
                    pyautogui.moveTo(x, y, duration=0.3) # dismiss hero hover information

                    randomWaitChance = 0.3
                    if random.random() < randomWaitChance:
                        interruptible_wait(round(random.uniform(5, 8), 2))

                    reselectChance = 0.3 if not state.SLOWER_PC_MODE else 0.2
                    if random.random() < reselectChance:
                        hero, hx2, hy2 = assetsLibrary.get_role_heroes_coord(role)
                        #logger.info(f"[INFO] Re-selecting {hero}")
                        pyautogui.moveTo(hx2, hy2, duration=0.3)

                        chance = 0.5 if not state.SLOWER_PC_MODE else 0.3
                        if random.random() < chance:
                            pyautogui.click()
                        else:
                            pyautogui.doubleClick()
                        pyautogui.moveTo(x, y, duration=0.3) # dismiss hero hover information
                        interruptible_wait(round(random.uniform(0.3, 0.6), 2))

                else:
                    pyautogui.doubleClick()
                    pyautogui.doubleClick()
                    logger.info(f"[INFO] {hero} selected")
                    pyautogui.moveTo(x, y, duration=0.3) # dismiss hero hover information
                    interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)

                # team chat
                if not state.SLOWER_PC_MODE:
                    pickingPhaseChat()
                    interruptible_wait(round(random.uniform(7, 11), 2))
                    continuePickingPhaseChat()            
            else:
                logger.info("[INFO] Bot decided to AFK")
                state.INGAME_STATE.setIsAfk(True)
                interruptible_wait(round(random.uniform(35, 45), 2))
                comebackChance = 0.2 if not state.SLOWER_PC_MODE else 0.15
                if random.random() < comebackChance:
                    state.INGAME_STATE.setIsAfk(False)
                    logger.info("[INFO] Bot is back from AFK")
                    hero, hx1, hy1 = assetsLibrary.get_role_heroes_coord(role)
                    logger.info(f"[INFO] Selecting {hero}")
                    pyautogui.moveTo(hx1, hy1, duration=0.3)
                    pyautogui.doubleClick()
                    x,y = assetsLibrary.get_picking_dismiss_safezone_coord()
                    pyautogui.moveTo(x, y, duration=0.3) # dismiss hero hover information

            logger.info("[INFO] Waiting to rageborn")
            # TODO: Alternative hero selection
            # TODO: Separated grief mode
            # if click_until_image_appears(f"heroes/{TARGETING_HERO}/picking-phase.png", [f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-legion.png",f"heroes/{TARGETING_HERO}/picking-phase-self-portrait-hellbourne.png"], 60, 0.5) == True:
            #     logger.info(f"[INFO] {TARGETING_HERO} selected")
            #     interruptible_wait(0.5)        
            #     pyautogui.moveTo(x, y, duration=0.3) # move off hover hero selection
            #     logger.info("[INFO] Waiting to rageborn")
            # else:
            #     # TODO: Random is just fine?
            #     logger.info(f"[INFO] {TARGETING_HERO} banned!")
            #     logger.info("[INFO] Waiting to get random hero.")


    while not state.STOP_EVENT.is_set():
        if any_image_exists(["ingame-top-left-menu-legion.png", "ingame-top-left-menu-hellbourne.png"], region=constant.SCREEN_REGION):
            logger.info("[INFO] I see fountain, I see grief!")
            logger.info("[INFO] Rageborn begin!")
            interruptible_wait(1.5 if not state.SLOWER_PC_MODE else 5)
            return True
        
        elif any_image_exists(["play-button.png", "play-button-christmas.png"], region=constant.SCREEN_REGION):
            # Back to lobby
            logger.info("[INFO] Match aborted!")
            return False
        
        interruptible_wait(2 if not state.SLOWER_PC_MODE else 2.5)

# pause vote
def do_pause_vote():
    pyautogui.click(1441, 221)
    interruptible_wait(0.05)
    pyautogui.click(1426, 261)
    interruptible_wait(0.05)
    pyautogui.click(1423, 319)
    return time.time()

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

    lane = LANE_BY_NUMBER[2] # constant mid lane only

    x1, y1 = assetsLibrary.get_friendly_tower_coord(map, team, lane, 3)
    x2, y2 = assetsLibrary.get_enemy_base_coord(map, team)

    # mouse cursor to team mid tower
    # alt+t and click to team mid tower
    # mouse cursor to enemy mid tower
    # right click to enemy mid tower

    pyautogui.moveTo(x1, y1, duration=0.15)
    pyautogui.hotkey("alt", "t")
    pyautogui.click()
    pyautogui.moveTo(x2, y2, duration=0.15)
    pyautogui.rightClick()

    return True

# FOC
def do_auto_following(x, y):
    #logger.info("[DEBUG] Auto following the lucky one..")
    pyautogui.keyUp("c") # stop center own hero            
    pyautogui.doubleClick(x, y)
    pyautogui.rightClick(960, 500)
    pyautogui.keyDown("c") # start center own hero

def allChat():
    import pyperclip
    team = state.INGAME_STATE.getCurrentTeam()
    opponent = constant.TEAM_HELLBOURNE if team == constant.TEAM_LEGION else constant.TEAM_LEGION
    randomString = [
        "yugen0x from discord community summon me!",
        "^:Having not a Steam release also is like wanting to fack and having no butt or other hole to put your cok !",
        "^:^rFAIL PC GAME - NO DEATH ANIMATIONS !",
        "^:Haven't had a maliken bot in a week now feels ^ggood",
        "I'm trolling because anyone genuinely believing there are bots in matchmaking is way ^rbelow intelligence average",
        "I have ^rragebbs in 10% of my games. Matchmaking is a complete ^:^yjoke.",
        "^:^988m a^977 l i^966 k e^955 n i^944 s a^933 n o^922 o b",
        "...",
        "WAHUEHAHHAHAHAUHAHAHAHEHAHAHAH!!",
        "^:I blame zaniir for his bot comment!",
        "demoasselborn Alan (777) proud to team up with me like you guys do ^r<3",
        "Stop being toxic and you won't get kicked Bub",
        "are they actually legit BOTS, or just someone pretending to be a BOT?",
        "^:Why is there a ^rkick vote ^999for toxic communication if free speech is the first thing in the code of conduct and there is a mute button?",
        "^:WELCOME TO HON REBORN GAMER!",
        "^:tollski love to have me in his game, you guys know that? secretly take a photo of me.. admire everywhere",
        "^:GOD, HOW AWFUL IS PLINKO 100% TICKET 0% CHEST!",
        f"^:Hey {opponent.upper()}! Enjoy your free MMR, come to mid lane get free kills",
        f"^:GET REKT NOOB LOSER BRAINDEAD ^r{team.upper()} TEAM.. ^999ENJOY YOUR BEST SHITTY GAME",
        "I doubt I was toxic in any of the games =)",
        "Now can you work on the bots on the AUS servers? ^:^ySure! More bots!",
        "^:Thank you once again for your time, we will see you in Newerth. ^y^:^_^",
        "im here to reward Atticah for getting a new monitor to play this retarded game!!!!",
        "^:unknownuser asked to push mid!! HERE I COME",
        "^:^966 ATTENTION ^999 Some content in this game may offend you Player discretion is advised",        
        "^:^966 ATTENTION ^999 Some content in this game may offend you Player discretion is advised"
    ]
    text = random.choice(randomString)
    pyperclip.copy(text)
    interruptible_wait(round(random.uniform(0.3, 0.5), 2))

    pyautogui.keyUp("c")
    pyautogui.hotkey("shift", "enter")
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    pyautogui.keyDown("c")

# FOC
def do_foc_stuff():
    import pyperclip
    #
    start_time = time.monotonic()
    team = getTeam()
    bought = False
    pyautogui.keyDown("c")
    
    # after 600 seconds will timeout and leave the game 
    matchTimedout = round(random.uniform(600, 660), 2)

    # vote pause    
    pauseChance = 0.2 
    if not state.SLOWER_PC_MODE and random.random() < pauseChance:
        state.INGAME_STATE.setIsAfk(True)
        randomString = [
            "sorry i need a pause.. 1 minute",
            "i need a pause",
            "1 pause",
            "1 pause please",
            "pause",
            "brb",
            "be right back",
            "zzzz somebody ring door",
            "brb phone call",
            "1 minute plz. on call"
        ]
        text = random.choice(randomString)
        pyperclip.copy(text)

        pyautogui.keyUp("c")
        acChance = 0.4 if not state.SLOWER_PC_MODE else 0.1
        if random.random() < acChance:
            pyautogui.hotkey("shift", "enter")
        else:
            pyautogui.press("enter")
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press("enter")
        pyautogui.keyDown("c")
        last_pause_time = do_pause_vote()
        interruptible_wait(round(random.uniform(40, 60), 2))
        start_time = time.monotonic()
    else:
        state.INGAME_STATE.setIsAfk(False)
        last_pause_time = time.time()
        afkChance = 0.15
        if not state.SLOWER_PC_MODE and random.random() < afkChance:
            state.INGAME_STATE.setIsAfk(True)
            logger.info("[INFO] Bot decided to go AFK ingame")
            time.sleep(round(random.uniform(30, 50), 2))

    #
    isPathSet = False
    pauseTimeout = 60 if not state.SLOWER_PC_MODE else 9000

    while not state.STOP_EVENT.is_set():
        isAfk = state.INGAME_STATE.getIsAfk()
        now = time.time() # for pause
        elapsed = time.monotonic() - start_time

        if not state.STOP_EVENT.is_set():           
            if now - last_pause_time >= pauseTimeout: # every 60s click
                do_pause_vote()
                last_pause_time = now

            if now - start_time >= 90: # every 90 seconds click tower defense
                pyautogui.keyUp("c")
                pyautogui.hotkey("alt", "b")
                pyautogui.keyDown("c")

        if not state.STOP_EVENT.is_set() and state.SCAN_VOTE_EVENT.is_set():
            state.SCAN_VOTE_EVENT.clear()

            if find_and_click("vote-no.png", region=constant.VOTE_REGION):
                reactChance = 0.4 if not state.SLOWER_PC_MODE else 0
                if not state.SLOWER_PC_MODE and not isAfk and random.random() < reactChance:
                    pyperclip.copy("why kick? Relax its beta...")
                    interruptible_wait(round(random.uniform(0.3, 0.5), 2)) if not state.SLOWER_PC_MODE else 1
                    pyautogui.keyUp("c")
                    pyautogui.hotkey("shift", "enter")
                    pyautogui.hotkey("ctrl", "v")
                    pyautogui.press("enter")
                    pyautogui.keyDown("c")

            if find_and_click("vote-no-black.png", region=constant.VOTE_REGION):
                reactChance = 0.4 if not state.SLOWER_PC_MODE else 0
                if not state.SLOWER_PC_MODE and not isAfk and random.random() < reactChance:
                    pyperclip.copy("why remake? Relax its beta...")
                    interruptible_wait(round(random.uniform(0.3, 0.5), 2)) if not state.SLOWER_PC_MODE else 1
                    pyautogui.keyUp("c")
                    pyautogui.hotkey("shift", "enter")
                    pyautogui.hotkey("ctrl", "v")
                    pyautogui.press("enter")
                    pyautogui.keyDown("c")
        
        if not state.STOP_EVENT.is_set() and not bought:
            # open ingame shop
            pyautogui.press("b")
            logger.info("[INFO] Opening ingame shop")
            interruptible_wait(round(random.uniform(0.3, 0.5), 2)) if not state.SLOWER_PC_MODE else 2

            # buy 500g mancher's boots
            pyautogui.rightClick(528, 628)
            logger.info("[INFO] Bought a Mancher cost 500g!")

            interruptible_wait(0.3) if not state.SLOWER_PC_MODE else 2
            # close ingame shop
            pyautogui.press("esc")
            logger.info("[INFO] Ingame shop closed")
            bought = True
            logger.info("[INFO] Waiting to get kick by the team...")
            interruptible_wait(round(random.uniform(0.3, 0.5), 2))
        
        if not state.STOP_EVENT.is_set():
            # remain silence until try vote pause to delay the kick
            if not state.SLOWER_PC_MODE and isAfk:
                state.INGAME_STATE.setIsAfk(False)
                do_pause_vote()
                last_pause_time = now

            isPathSet = do_lane_push_step(team)

            # TODO: spam taunt (need to calculate or know already ready tower)    
            # TODO: death recap or respawn time show then stop spam

        if not state.SLOWER_PC_MODE and not state.STOP_EVENT.is_set() and isPathSet:
            allChatSpamChance = 0.8 
            if not isAfk and random.random() < allChatSpamChance:
                delayChance = 0.45
                if random.random() < delayChance:
                    interruptible_wait(round(random.uniform(1, 1.5), 2))
                allChat()
                isPathSet = False

        if not state.STOP_EVENT.is_set() and state.SCAN_LOBBY_MESSAGE_EVENT.is_set():
            state.SCAN_LOBBY_MESSAGE_EVENT.clear()

            if check_lobby_message():    
                pyautogui.keyUp("c") # stop spamming
                state.STOP_EVENT.set()
                break
        
        if elapsed >= matchTimedout:    
            pyautogui.keyUp("c") # stop spamming
            logger.info(f"[TIMEOUT] {matchTimedout} seconds reached. Stopping.")
            state.STOP_EVENT.set()
            break

        interruptible_wait(0.03 if not state.SLOWER_PC_MODE else 0.15)

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
        f"{constant.DIALOG_MESSAGE_DIR}/no-response-from-server-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/not-the-roaster-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/rst-stream-error-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/match-already-in-progress-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/host-started-the-game-while-not-in-team-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/unable-to-enter-matchmaking-queue-message.png"
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
        pin_jokevio()

        # Account Login manually
        if account_Login(username, password):
            while not state.STOP_EVENT.is_set():
                #
                prequeue()

                #
                isEnterPickingPhase = startQueue()
                if not isEnterPickingPhase:
                    logger.warning("[INFO] Queue cooldown! Aborting..")
                    state.STOP_EVENT.set()
                    break
                
                #
                result = pickingPhase()          

                if not result:

                    messageClearTime = 5 if not state.SLOWER_PC_MODE else 10
                    while not state.STOP_EVENT.is_set():
                        if not check_lobby_message():
                            break
                        find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION)
                        interruptible_wait(0.5)
                        messageClearTime -= 0.5
                        if messageClearTime <= 0:
                            break                        

                    logger.warning("[QUEUE] Match aborted, restarting queue")
                    continue

                ingame()

        logger.info("[INFO] Rageborn shutting down...")
    
    finally:
        unpin_jokevio() 
