import pyautogui
import time
import win32gui
import win32con
import win32process
import psutil
import threading
import utilities.constants as constant
import core.state as state
import utilities.coordinateAccess as assetsLibrary
import random
import subprocess

from pathlib import Path
from threads.hwnd_watchdog import start_hwnd_watchdog
from utilities.loggerSetup import setup_logger
from threads.ingame import vote_requester, lobby_message_check_requester
from utilities.common import interruptible_wait, interruptible_wait
from utilities.imagesUtilities import find_and_click, image_exists, any_image_exists, image_exists_in_any_region
from utilities.datasetLoader import load_dataset
from utilities.common import resource_path
from utilities.chatUtilities import get_picking_chats, get_ingame_chats, apply_chat_placeholders
from utilities.accountGenerator import generatePendingAccount
from utilities.networkUtilities import getDisconnected, reconnect, wait_for_ping
from utilities.capture.screen_capture import capture_fullscreen
from utilities.ui.draft_screen_regions import crop_draft_team_regions
from utilities.ocr.ocr_engine import read_usernames_from_region, normalize_username, fix_common_ocr_errors
from utilities.paths import get_launcher_dir
from difflib import SequenceMatcher


# Initialize Logger
logger = setup_logger()


logger.info(f"[DEBUG] CWD = {Path.cwd()}")
logger.info(f"[DEBUG] launcher_dir = {get_launcher_dir()}")

from utilities.config import load_config
# Load Config at startup
load_config()

# Safety: Move mouse to top-left to abort
pyautogui.FAILSAFE = True

# Mouse/Keyboard Input Settings
pyautogui.PAUSE = 0.3

# Load Dataset
COORDS = load_dataset("coordinates_1920x1080")
assetsLibrary.init(COORDS)

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

        if state.RAGEQUIT_MODE:
            logger.info("[INFO] RAGEQUIT MODE ENABLED")

        #
        main(username, password, isRageQuit=state.RAGEQUIT_MODE)
    finally:
        logger.info("[MAIN] shutting down")        
        stop_powershell()
        state.STOP_EVENT.set()

        for t in threads:
            t.join()

#
def find_juvio_platform_hwnd():
    """
    Find visible window handles for the game launcher / client.

    Accepts multiple possible window titles because the launcher title
    may change over time (e.g. rebranding).
    """
    TARGET_TITLES = (
        "juvio platform",
        "heroes of newerth",
    )

    hwnds = []

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)
        if not title:
            return

        title_lc = title.lower()

        if any(t in title_lc for t in TARGET_TITLES):
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
    ps_priority_proc = None
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
    interruptible_wait(0.7)
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

def startQueue(isRageQuit: bool = False):
    interruptible_wait(1.25 if not isRageQuit else 0.5)

    #
    isReInitiated = state.INGAME_STATE.getIsReInitiated()

    # Tune matchmaking bar
    if not isReInitiated:
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
    pyautogui.moveTo(x, y, duration=0.1)
    interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
    pyautogui.click()    
    interruptible_wait(1.5 if not state.SLOWER_PC_MODE else 3)
    logger.info("[INFO] Queue started. Waiting to get a match..")

    while not state.STOP_EVENT.is_set():

        if find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
            interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
            pass

        if not image_exists("matchmaking-panel-header.png", region=constant.SCREEN_REGION) and any_image_exists(["play-button.png", "play-button-christmas.png"], region=constant.SCREEN_REGION):
            if find_and_click("play-button.png", region=constant.SCREEN_REGION):
                interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
            
            if find_and_click("play-button-christmas.png", region=constant.SCREEN_REGION):
                interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)

            if image_exists("enter-queue.png", region=constant.SCREEN_REGION):
                pyautogui.moveTo(x, y, duration=0.3)
                interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
                pyautogui.click()

        # Requeue
        if not image_exists("waiting-for-players.png", region=constant.SCREEN_REGION) and image_exists("enter-queue.png", region=constant.SCREEN_REGION):
            logger.info("[INFO] Still seeing PLAY button.. Re-queueing..")
            pyautogui.moveTo(x, y, duration=0.3)
            interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
            pyautogui.click()

        # if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/failed-to-fetch-mmr-message.png", region=constant.LOBBY_MESSAGE_REGION):
        #     logger.info("[INFO] 'Failed to fetch mmr' message showed!")
        #     if find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
        #         logger.info("[INFO] Message dismissed!")
        #         pyautogui.moveTo(x, y, duration=0.3)
        #         interruptible_wait(0.3 if not state.SLOWER_PC_MODE else 1)
        #         pyautogui.click()
        #     else:
        #         logger.info("[ERROR] Unable to locate OK button.")

        # if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/taken-too-long-message.png", region=constant.LOBBY_MESSAGE_REGION):
        #     interruptible_wait(2 if not state.SLOWER_PC_MODE else 2.5)
        #     logger.info("[INFO] 'Waiting taken too long' message showed!")
        #     if find_and_click("message-ok.png"):
        #         logger.info("[INFO] Message dismissed!")
        #     else:
        #         logger.info("[ERROR] Unable to locate OK button.")

        # if image_exists(f"{constant.DIALOG_MESSAGE_DIR}/not-a-host-message.png", region=constant.LOBBY_MESSAGE_REGION):
        #     interruptible_wait(2 if not state.SLOWER_PC_MODE else 2.5)
        #     logger.info("[INFO] 'Not a host' message showed!")
        #     if find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
        #         logger.info("[INFO] Message dismissed!")
        #     else:
        #         logger.info("[ERROR] Unable to locate OK button.")
                
        # successfully joined a match: FOC
        if any_image_exists([
            "foc-role-info.png",
            "choose-a-hero-button.png"
        ]):
            logger.info("[INFO] Match found! Mode: Forest of Cunt!")
            state.INGAME_STATE.setCurrentMap(constant.MAP_FOC)
            interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)
            return True
        
        if any_image_exists([
            "mw-ban-a-hero-button.png"
        ]):
            logger.info("[INFO] Match found! Mode: Midwar!")
            state.INGAME_STATE.setCurrentMap(constant.MAP_MIDWAR)
            interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 1)
            return True        
        
        if image_exists("queue-cooldown.png", region=constant.SCREEN_REGION):
            return False

        interruptible_wait(1 if not state.SLOWER_PC_MODE else 1.5)



def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def getTeam():
    interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 3)

    SIMILARITY_THRESHOLD = 0.80  # 🔒 tune once, do not guess

    screenshot = capture_fullscreen()
    regions = crop_draft_team_regions(screenshot)

    my_username = state.INGAME_STATE.getUsername()
    if not my_username:
        logger.error("[ERROR] Username not set")
        return False

    my_username = fix_common_ocr_errors(
        normalize_username(my_username.lower().strip())
    )

    best_match = None  # 🔑 single source of truth

    for team, region in regions.items():
        if region is None:
            continue

        rows = read_usernames_from_region(region, team)

        for row in rows:
            index = row.get("row")
            text = row.get("text", "").lower().strip()
            if not text:
                continue

            logger.warning(
                f"[MATCH-DEBUG] team={team} pos={index} "
                f"me='{my_username}' ocr='{text}'"
            )

            # ---------- STRICT MATCH ----------
            if my_username in text or text in my_username:
                score = 1.0  # 🔒 absolute win
                match_type = "strict"
            else:
                # ---------- FUZZY MATCH ----------
                score = similarity(my_username, text)
                match_type = "fuzzy"

                if score < SIMILARITY_THRESHOLD:
                    continue

            logger.debug(
                f"[MATCH-CANDIDATE] pos={index} "
                f"type={match_type} score={score:.2f}"
            )

            candidate = {
                "team": team,
                "position": index,
                "text": text,
                "score": score,
                "type": match_type,
            }

            # 🔥 Keep only the best candidate
            if (
                best_match is None
                or candidate["score"] > best_match["score"]
            ):
                best_match = candidate

    # ---------- FINAL DECISION ----------
    if not best_match:
        logger.warning("[INFO] Failed to detect team via OCR")
        return False

    logger.info(
        f"[FINAL-MATCH] team={best_match['team']} "
        f"pos={best_match['position']} "
        f"type={best_match['type']} "
        f"score={best_match['score']:.2f}"
    )

    state.INGAME_STATE.setCurrentTeam(best_match["team"])
    state.INGAME_STATE.setPosition(best_match["position"])
    return True


# def getTeam():
#     interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 3)
    # team = constant.TEAM_LEGION # Default

    # match state.INGAME_STATE.getCurrentMap():
    #     case constant.MAP_FOC:
    #         # click minimap
    #         pyautogui.click(511,792)
    #         interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 4)
    #         if any_image_exists([
    #             "foc-mid-tower-legion.png"
    #             ]):
    #             team = constant.TEAM_LEGION
    #         else:
    #             team = constant.TEAM_HELLBOURNE

    #     case constant.MAP_MIDWAR:
    #         pyautogui.click(505, 798)
    #         interruptible_wait(0.5 if not state.SLOWER_PC_MODE else 4)
    #         if any_image_exists([
    #             "mw-legion-mid-tower-sight.png"
    #             ]):
    #             team = constant.TEAM_LEGION
    #         else:
    #             team = constant.TEAM_HELLBOURNE
    
    # state.INGAME_STATE.setCurrentTeam(team)
    # logger.info(f"[INFO] We are on {team} team!")
    # interruptible_wait(1 if not state.SLOWER_PC_MODE else 2)
    # pyautogui.press("c")    
    #return team

def enterChat(text):
    pyautogui.moveTo(921, 831)
    pyautogui.click()
    type_text(text=text, enter=True)

def pickingPhaseChat(isRageQuit: bool = False):
    if not isRageQuit:
        chatChance = 0.5 if not state.SLOWER_PC_MODE else 0.3 
        if random.random() < chatChance:
            # TODO: in sequence or random
            randomString = get_picking_chats()
            if not randomString:
                return

            text = random.choice(randomString)
            text = apply_chat_placeholders(text)        
            enterChat(text)
    else:
        isReInitiated = state.INGAME_STATE.getIsReInitiated()

        randomString = get_picking_chats()
        if not randomString:
            return
        
        if not isReInitiated:
            pyautogui.click(1068, 836) # toggle chat to all
        text = random.choice(randomString)
        text = apply_chat_placeholders(text)
        enterChat(text)

        spamTimeout = round(random.uniform(3, 7), 2)
        start = time.time()

        while not state.STOP_EVENT.is_set():
            if time.time() - start >= spamTimeout:
                break

            pyautogui.press("up")
            pyautogui.press("enter")

            # sleep BUT remain interruptible
            if interruptible_wait(0.05):
                break

    return True

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


def generateAccount():
    while not state.STOP_EVENT.is_set():
        status, username, password = generatePendingAccount()
        if status:
            logger.info(f"[INFO] Generated Username: {username}")
            break

        interruptible_wait(1 if not state.SLOWER_PC_MODE else 2)

    return username, password
    

def pickingPhase(isRageQuit: bool = False):

    # Just in case
    if image_exists("message-ok.png", region=constant.LOBBY_MESSAGE_REGION):
        find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION)
        interruptible_wait(0.5)

    if not isRageQuit:
        logger.info("[INFO] Getting team information")
        getTeam()

    generateAccount()
    
    if isRageQuit:
        # Ragequit
        logger.info("[INFO] Waiting to change account")
        interruptible_wait(round(random.uniform(1, 3), 2))

        return True    
    else:
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
                        pickingPhaseChat(isRageQuit)
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

            case constant.MAP_MIDWAR:
                x,y = assetsLibrary.get_picking_dismiss_safezone_coord()
                interruptible_wait(round(random.uniform(5, 10), 2))
                logger.info("[INFO] Waiting banning phase.")
                hero, bx, by = assetsLibrary.get_heroes_coord(random_pick=True)
                pyautogui.moveTo(bx, by, duration=0.3)
                pyautogui.doubleClick()
                logger.info(f"[INFO] Hero {hero} is now banned!")
                logger.info("[INFO] Waiting picking phase.")
                interruptible_wait(round(random.uniform(1, 5), 2))
                pyautogui.moveTo(x, y, duration=0.3)

                while not state.STOP_EVENT.is_set():
                    if image_exists("choose-a-hero-button.png"):
                        break

                    interruptible_wait(round(random.uniform(1, 2), 2))

                logger.info("[INFO] Picking phase.")
                interruptible_wait(round(random.uniform(10, 30), 2))
                hero, bx, by = assetsLibrary.get_heroes_coord(random_pick=True)
                pyautogui.moveTo(bx, by, duration=0.3)
                pyautogui.doubleClick()
                logger.info(f"[INFO] Hero {hero} is now selected!")
                pyautogui.moveTo(x, y, duration=0.3)
    
    logger.info("[INFO] Waiting to rageborn")
    while not state.STOP_EVENT.is_set():
        if any_image_exists(["ingame-top-left-menu-legion.png", "ingame-top-left-menu-hellbourne.png"], region=constant.SCREEN_REGION):
            logger.info("[INFO] I see fountain, I see grief!")
            logger.info("[INFO] Rageborn begin!")
            interruptible_wait(0.08)
            do_pause_vote() # avoiding teammate to kick and drag their time so can give them PP
            do_pp_stuff()
            interruptible_wait(1.5 if not state.SLOWER_PC_MODE else 5)
            return True
        
        if any_image_exists(["play-button.png", "play-button-christmas.png"], region=constant.SCREEN_REGION):
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

# Mw
def do_mw_lane_push_step(team):
    map = state.INGAME_STATE.getCurrentMap()
    x1, y1 = assetsLibrary.get_enemy_fountain_coord(map, team)

    # mouse cursor to team mid tower
    # alt+t and click to team mid tower
    # mouse cursor to enemy mid tower
    # right click to enemy mid tower

    pyautogui.moveTo(x1, y1, duration=0.15)
    pyautogui.hotkey("alt", "t")
    pyautogui.click()
    pyautogui.moveTo(x1, y1, duration=0.15)
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
    # TODO: in sequence or random
    randomString = get_ingame_chats()
    if not randomString:
        return

    text = random.choice(randomString)
    text = apply_chat_placeholders(text)
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
    #team = getTeam()
    team = state.INGAME_STATE.getCurrentTeam()
    bought = False
    pyautogui.keyDown("c")
    
    # after 600 seconds will timeout and leave the game 
    matchTimedout = round(random.uniform(600, 660), 2)

    # vote pause    
    # pauseChance = 0.2 
    # if not state.SLOWER_PC_MODE and random.random() < pauseChance:
    #     state.INGAME_STATE.setIsAfk(True)
    #     randomString = [
    #         "sorry i need a pause.. 1 minute",
    #         "i need a pause",
    #         "1 pause",
    #         "1 pause please",
    #         "pause",
    #         "brb",
    #         "be right back",
    #         "zzzz somebody ring door",
    #         "brb phone call",
    #         "1 minute plz. on call"
    #     ]
    #     text = random.choice(randomString)
    #     pyperclip.copy(text)

    #     pyautogui.keyUp("c")
    #     acChance = 0.4 if not state.SLOWER_PC_MODE else 0.1
    #     if random.random() < acChance:
    #         pyautogui.hotkey("shift", "enter")
    #     else:
    #         pyautogui.press("enter")
    #     pyautogui.hotkey("ctrl", "v")
    #     pyautogui.press("enter")
    #     pyautogui.keyDown("c")
    #     last_pause_time = do_pause_vote()
    #     interruptible_wait(round(random.uniform(40, 60), 2))
    #     start_time = time.monotonic()
    # else:
    #     state.INGAME_STATE.setIsAfk(False)
    #     last_pause_time = time.time()
    #     afkChance = 0.15
    #     if not state.SLOWER_PC_MODE and random.random() < afkChance:
    #         state.INGAME_STATE.setIsAfk(True)
    #         logger.info("[INFO] Bot decided to go AFK ingame")
    #         time.sleep(round(random.uniform(30, 50), 2))
    
    last_pause_time = time.time()

    #
    isPathSet = False
    pauseTimeout = 60 if not state.SLOWER_PC_MODE else 9000

    while not state.STOP_EVENT.is_set():
        isAfk = state.INGAME_STATE.getIsAfk()
        now = time.time() # for pause
        elapsed = time.monotonic() - start_time
        
        if elapsed >= matchTimedout:    
            pyautogui.keyUp("c") # stop spamming
            logger.info(f"[TIMEOUT] {matchTimedout} seconds reached. Stopping.")
            break

        if not state.STOP_EVENT.is_set() and state.SCAN_LOBBY_MESSAGE_EVENT.is_set():
            state.SCAN_LOBBY_MESSAGE_EVENT.clear()

            if check_lobby_message():    
                pyautogui.keyUp("c") # stop spamming
                break

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

        interruptible_wait(0.03 if not state.SLOWER_PC_MODE else 0.15)

    return True


def leaveMatch():
    pyautogui.click(1454, 224)
    interruptible_wait(0.08)
    pyautogui.click(1430, 304)
    interruptible_wait(0.08)
    pyautogui.click(993, 442)
    interruptible_wait(2)
    pyautogui.click(995, 340)
    interruptible_wait(0.08)


# Midwar
def do_midwar_stuff():
    import pyperclip
    #
    start_time = time.monotonic()
    #team = getTeam()
    team = state.INGAME_STATE.getCurrentTeam()
    bought = False
    pyautogui.keyDown("c")
    
    # after 600 seconds will timeout and leave the game 
    matchTimedout = round(random.uniform(600, 660), 2)
    last_pause_time = time.time()
    pauseTimeout = 60

    while not state.STOP_EVENT.is_set():
        isAfk = state.INGAME_STATE.getIsAfk()
        now = time.time() # for pause
        elapsed = time.monotonic() - start_time
        
        if elapsed >= matchTimedout:    
            pyautogui.keyUp("c") # stop spamming
            logger.info(f"[TIMEOUT] {matchTimedout} seconds reached. Stopping.")
            break

        if not state.STOP_EVENT.is_set() and state.SCAN_LOBBY_MESSAGE_EVENT.is_set():
            state.SCAN_LOBBY_MESSAGE_EVENT.clear()

            if check_lobby_message():    
                pyautogui.keyUp("c") # stop spamming
                break

        if not state.STOP_EVENT.is_set():           
            if now - last_pause_time >= pauseTimeout: # every 60s click
                do_pause_vote()
                last_pause_time = now            

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

            isPathSet = do_mw_lane_push_step(team)

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

        interruptible_wait(0.03 if not state.SLOWER_PC_MODE else 0.15)

    return True


# PP
def do_pp_stuff():
    logger.info("[INFO] Giving free PP points!")

    team = state.INGAME_STATE.getCurrentTeam()
    my_pos = state.INGAME_STATE.getPosition()  # 1–5

    type_in_order = [
        constant.PP_PLAYER_ROW_COG,
        constant.PP_AVOID_PLAYER,
        constant.PP_MUTE_CHAT,
        constant.PP_MUTE_VOICE
    ]

    pyautogui.keyDown("x")
    interruptible_wait(0.15)

    try:        
        for pos in range(1, 6):
            if pos == my_pos:
                continue

            for pp_type_index, pp_type in enumerate(type_in_order):
                x, y = assetsLibrary.get_pp_type_coord(
                    team=team,
                    pos=pos,
                    type=pp_type
                )

                pyautogui.moveTo(x, y, duration=0.08)
                pyautogui.click()
                interruptible_wait(0.08)

                if pp_type_index == 1:
                    dialog = assetsLibrary.get_avoid_dialog_coords()

                    pyautogui.moveTo(dialog["dropdown"]["x"], dialog["dropdown"]["y"], duration=0.08)
                    pyautogui.click()
                    pyautogui.moveTo(dialog["reason"]["x"], dialog["reason"]["y"], duration=0.08)
                    pyautogui.click()

                    if not find_and_click("pp-dialog-confirm-button.png", region=constant.SCREEN_REGION):
                        pyautogui.moveTo(dialog["confirm"]["x"], dialog["confirm"]["y"], duration=0.08)
                        pyautogui.click()

                # Optional: debug / conditional logic
                # logger.debug(f"PP[{pp_type_index}] {pp_type} on pos {pos}")

    finally:
        pyautogui.keyUp("x")


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
        f"{constant.DIALOG_MESSAGE_DIR}/unable-to-enter-matchmaking-queue-message.png",
        f"{constant.DIALOG_MESSAGE_DIR}/group-on-cooldown-message.png"
    ], region=constant.LOBBY_MESSAGE_REGION)        

def ingame(): 
    #
    logger.info("[INFO] HERE COMES THE TROLL BEGIN")

    isSuccess = False
    match state.INGAME_STATE.getCurrentMap():
        case constant.MAP_FOC:
            isSuccess = do_foc_stuff()

        case constant.MAP_MIDWAR:
            isSuccess = do_midwar_stuff()

    return isSuccess

def changeAccount(isRageQuit: bool = False):
    interruptible_wait(round(random.uniform(0.2, 1), 2))
    acc = state.get_latest_pending_account()

    if not acc:
        logger.error("[ERROR] No pending account to change, aborting..")
        state.increment_iteration()
        state.STOP_EVENT.set() # quit loop

    if isRageQuit:
        timedoutChance = 0.8
        if random.random() < timedoutChance:
            adapter = getDisconnected()
            logger.info("[INFO] Oops! electricity goes off out of sudden")
                
            reconnect(adapter)
            logger.info("[INFO] Waiting to reconnect...")
            restored = wait_for_ping(timeout=30)
            if restored:
                logger.info("[INFO] Got back connection!")
                # pyautogui.click(1415, 235)
                # pyautogui.click(1000, 425)
                # interruptible_wait(2)
                # pyautogui.click(991, 341)
                interruptible_wait(5.5)


            while not state.STOP_EVENT.is_set():
                if image_exists("startup/login-button.png", region=constant.SCREEN_REGION):
                    logger.info("[INFO] Timed-out to login page..")
                    break

                if any_image_exists(["play-button.png", "play-button-christmas.png"], region=constant.SCREEN_REGION):
                    logger.info("[INFO] Manually logout after timeout!")
                    pyautogui.click(1415, 235) #logout
                    break

                interruptible_wait(0.3)
            
            interruptible_wait(4)
        else:
            logger.info("[INFO] Ready to disconnect..")
            interruptible_wait(round(random.uniform(5, 10), 2))
            pyautogui.click(1415, 235)
            pyautogui.click(1000, 425)
            interruptible_wait(2)
            pyautogui.click(991, 341)
            interruptible_wait(1)

            # logout
            pyautogui.click(1415, 235)
            interruptible_wait(0.5)
    else:
        pyautogui.click(1415, 235)
        interruptible_wait(0.5)

    # Make sure it has been logged out
    if not image_exists("startup/login-button.png", region=constant.SCREEN_REGION):
        pyautogui.click(1415, 235)
        interruptible_wait(0.5)    

    # Increase complete count
    state.increment_iteration()

    # Re-enter username field
    pyautogui.doubleClick(1010, 568)

    if not acc or not isinstance(acc.username, str):
        logger.error(f"[CHANGE] Invalid pending account: {acc}")
        state.STOP_EVENT.set()
        return False

    type_text(acc.username)
    pyautogui.press("tab")
    pyautogui.press("enter")
    logger.info("[INFO] Attempt to login")
    
    timeout = 10
    loginTime = time.time()
    while not state.STOP_EVENT.is_set():
        now = time.time()

        if image_exists("startup/login-button.png", region=constant.SCREEN_REGION):    
            logger.info("[INFO] Reattempt to login")
            pyautogui.click(1010, 568)
            pyautogui.press("tab")
            pyautogui.press("enter")
            break

        if any_image_exists([
            "play-button.png", "play-button-christmas.png"
            ], region=constant.SCREEN_REGION):
            logger.info(f"[LOGIN] Successfully logged in as {acc.username}")
            state.INGAME_STATE.setIsReInitiated(True)
            state.clear_pending_account(acc.username)
            break

        if now - loginTime >= timeout:
            logger.info("[INFO] Seems stucked, aborting iteration.")
            state.STOP_EVENT.set() # TODO 
            break

    return True

#
def main(username, password, isRageQuit: bool = False):
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
                if isEnterPickingPhase:
                    #
                    result = pickingPhase(isRageQuit)

                    if not isRageQuit and not result:
                        # Rageborn match aborted
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

                    if not isRageQuit:
                        ingame()

                        if not any_image_exists(["play-button.png", "play-button-christmas.png"], region=constant.SCREEN_REGION):                            
                            logger.info("[INFO] Manually leave the match due to match timeout reached.")
                            leaveMatch()

                        else:
                            find_and_click("message-ok.png", region=constant.LOBBY_MESSAGE_REGION)
                            logger.info("[INFO] KICKED! Closing dialog message.")

                else:
                    logger.warning("[INFO] Queue cooldown! Changing account..")
                    generateAccount()
                
                # TODO: if want to use existing account can skip this step so it will loop
                changeAccount(isRageQuit)

        logger.info("[INFO] Rageborn shutting down...")
    
    finally:
        unpin_jokevio() 
