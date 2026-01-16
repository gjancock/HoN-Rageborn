import logging
import tkinter as tk
from tkinter import messagebox
import requests
import re
from urllib.parse import urlencode
import random
import subprocess
import threading
import time
from datetime import datetime
import sys
import os
from queue import Queue
from utilities.loggerSetup import setup_logger
import core.state as state
from utilities.config import load_config
# Load Config at startup
load_config()
from utilities.usernameGenerator import generate_word_username, generate_random_string
from requests.exceptions import ConnectionError, Timeout
from http.client import RemoteDisconnected
import configparser
import pyautogui
from utilities.common import resource_path
from requests.exceptions import RequestException
from utilities.ipAddressGenerator import random_public_ip
from tkinter import filedialog
from tkinter import ttk
from utilities.accountVerification import AccountVerifier
from utilities.gameConfigUtilities import prepare_game_config
import time
import subprocess
import sys
import socket
import requests
import psutil

# Logger
log_queue = Queue()
logger = setup_logger(ui_queue=log_queue)
ui_formatter = logging.Formatter(
    "%(asctime)s | %(message)s",
    "%H:%M:%S"
)

#
auto_start_time = None
iteration_count = 0

#
BASE_URL = "https://app.juvio.com"
SIGNUP_URL = BASE_URL + "/signup"

#
MIN_USERNAME_LENGTH = 2
MAX_USERNAME_LENGTH = 16

#
DEFAULT_FIRST_NAME = "Maliken"
DEFAULT_LAST_NAME = "DeForest"
DEFAULT_PASSWORD = "@Abc12345"

#
auto_start_timer_id = None
AUTO_START_DELAY_MS = 5000  # 5 seconds
auto_start_countdown_id = None
AUTO_START_DELAY_SECONDS = 5
auto_start_remaining = 0


def exe_dir():
    if getattr(sys, "frozen", False):
        # Running as PyInstaller exe
        return os.path.dirname(sys.executable)
    else:
        # Running as normal Python script
        return os.path.dirname(os.path.abspath(__file__))

# ============================================================
# APPLICATION SETTINGS
# ============================================================
def set_self_high_priority():
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        logger.info("[PRIORITY] Python process set to HIGH")

    except psutil.AccessDenied:
        logger.warning("[PRIORITY] Access denied – priority unchanged")

    except Exception as e:
        logger.warning(f"[PRIORITY] Failed to set priority: {e}")


def global_thread_exception_handler(args):
    logger.exception(
        "[THREAD-CRASH] Unhandled exception",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )

threading.excepthook = global_thread_exception_handler

def get_runtime_dir():
    if getattr(sys, "frozen", False):
        # PyInstaller EXE location
        return os.path.dirname(sys.executable)
    else:
        # Python script location
        return os.path.dirname(os.path.abspath(__file__))


def read_version():
    try:
        path = os.path.join(exe_dir(), "VERSION")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        logger.error("[ERROR] Unable to find VERSION")
        return "unknown"
    
#
INFO_NAME = "Rageborn"
VERSION = read_version()

# ============================================================
# CONFIG (INI)
# ============================================================

CONFIG_FILE = os.path.join(get_runtime_dir(), "config.ini")

def read_auto_update():
    path = os.path.join(exe_dir(), "config.ini")
    config = configparser.ConfigParser()

    try:
        config.read(path, encoding="utf-8")
        return config.getboolean("settings", "auto_update", fallback=True)
    except Exception:
        return True  # safe default


def get_auto_start_endless():
    return state.AUTO_START_ENDLESS

def get_game_executable():
    return state.GAME_EXECUTABLE

def get_auto_email_verification():
    return state.AUTO_EMAIL_VERIFICATION

def get_auto_mobile_verification():
    return state.AUTO_MOBILE_VERIFICATION

def get_auto_restart_dns():
    return state.AUTO_RESTART_DNS

def get_auto_update():
    return state.AUTO_UPDATE

def get_settings_for_slower_pc():
    return state.SLOWER_PC_MODE

def set_auto_start_endless(value: bool):
    state.AUTO_START_ENDLESS = value

    config = configparser.ConfigParser()
    path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(path):
        config.read(path)

    if "endless" not in config:
        config["endless"] = {}

    config["endless"]["auto_start"] = "true" if value else "false"

    with open(path, "w") as f:
        config.write(f)


def set_game_executable(executable_path: str):
    # 1️⃣ Update runtime state
    state.GAME_EXECUTABLE = executable_path

    # 2️⃣ Prepare config
    config = configparser.ConfigParser()
    config_path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(config_path):
        config.read(config_path)

    if "paths" not in config:
        config["paths"] = {}

    # 3️⃣ Write correct value
    config["paths"]["game_executable"] = executable_path

    # 4️⃣ Save
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)


def set_auto_email_verification(value: bool):
    state.AUTO_EMAIL_VERIFICATION = value
    config = configparser.ConfigParser()
    path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(path):
        config.read(path)

    if "verification" not in config:
        config["verification"] = {}
    config["verification"]["auto_email"] = "true" if value else "false"
    with open(path, "w") as f:
        config.write(f)


def set_auto_mobile_verification(value: bool):
    state.AUTO_MOBILE_VERIFICATION = value
    config = configparser.ConfigParser()
    path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(path):
        config.read(path)

    if "verification" not in config:
        config["verification"] = {}
    config["verification"]["auto_mobile"] = "true" if value else "false"
    with open(path, "w") as f:
        config.write(f)


def set_auto_restart_dns(value: bool):
    state.AUTO_RESTART_DNS = value
    config = configparser.ConfigParser()
    path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(path):
        config.read(path)

    if "network" not in config:
        config["network"] = {}
    config["network"]["auto_restart_dns"] = "true" if value else "false"
    with open(path, "w") as f:
        config.write(f)


def set_auto_update(enabled: bool):
    state.AUTO_UPDATE = enabled
    config = configparser.ConfigParser()
    path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(path):
        config.read(path)

    if "settings" not in config:
        config["settings"] = {}
    config["settings"]["auto_updates"] = "true" if enabled else "false"
    with open(path, "w") as f:
        config.write(f)


def set_settings_for_slower_pc(value: bool):
    state.SLOWER_PC_MODE = value
    config = configparser.ConfigParser()
    path = os.path.join(exe_dir(), "config.ini")

    if os.path.exists(path):
        config.read(path)

    if "performance" not in config:
        config["performance"] = {}
    config["performance"]["slower_pc_mode"] = "true" if value else "false"
    with open(path, "w") as f:
        config.write(f)


# ============================================================
# SIGNUP LOGIC (NO UI CODE HERE)
# ============================================================

def is_signup_success(r):
    try:
        data = r.json()
    except ValueError:
        return False, "Invalid JSON response"

    if data.get("status") != "success":
        return False, "Failed to signup: username existed or email used"

    tokens = data.get("tokens", "")
    if "csrf-token" not in tokens:
        return False, "Missing CSRF token"

    return True, "Signup success"


def is_dns_error(exc: Exception) -> bool:
    """
    Detect DNS-related failures safely.
    """
    msg = str(exc).lower()

    return (
        isinstance(exc, requests.exceptions.ConnectionError)
        and (
            "getaddrinfo failed" in msg
            or "name or service not known" in msg
            or "failed to resolve" in msg
        )
    ) or isinstance(exc, socket.gaierror)


def restart_windows(reason: str = ""):
    """
    Restart Windows immediately.
    """
    logger.critical("[SYSTEM] Restarting Windows due to DNS failure")
    if reason:
        logger.critical(f"[SYSTEM] Reason: {reason}")

    # Force immediate restart
    subprocess.run(
        ["shutdown", "/r", "/t", "0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Hard exit if shutdown is blocked
    sys.exit(1)


def safe_get(
    session,
    url,
    retries=3,
    delay=3,
    restart_on_dns=False  # 🔥 toggle flag
):
    last_exception = None

    for i in range(retries):
        try:
            return session.get(url, timeout=15)

        except Exception as e:
            last_exception = e
            logger.warning(
                f"[RETRY] GET failed ({i+1}/{retries}): {e}"
            )

            # Immediate escalation if DNS issue
            if is_dns_error(e):
                logger.error("[NETWORK] DNS resolution failure detected")

                if restart_on_dns:
                    restart_windows(reason=str(e))

                break  # do not keep retrying DNS failures

            time.sleep(delay)

    raise RuntimeError(
        "DNS resolution failed after retries"
        if is_dns_error(last_exception)
        else "HTTP GET failed after retries"
    )

def start_account_verification_async(username: str):
    def worker():
        try:
            logger.info(f"[INFO] Starting verification process for {username}")
            verifier = AccountVerifier(logger)
            verifier.run(
                mobile=get_auto_mobile_verification(),
                email=get_auto_email_verification()
            )
            logger.info(f"[INFO] Account verification completed.")
        except Exception:
            logger.exception("[ERROR] Verification failed")

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


def signup_user(first_name, last_name, email, username, password):
    session = requests.Session()
    session.headers.update({
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "Chrome/143.0.0.0"
        )
    })

    try:
        # 1️⃣ GET signup page
        resp = safe_get(session, SIGNUP_URL, restart_on_dns=get_auto_restart_dns())
        resp.raise_for_status()

        match = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
        if not match:
            logger.error("[ERROR] Failed to get CSRF token.")
            return False, "CSRF not found"

        csrf = match.group(1)

        fakeIp = random_public_ip()

        payload = {
            "_csrf": csrf,
            "User[first_name]": first_name,
            "User[last_name]": last_name,
            "User[email]": email,
            "User[display_name]": first_name,
            "User[username]": username,
            "User[password]": password,
            "User[repeat_password]": password,
            "User[role_id]": "player",
            "User[timezone_id]": 1,
            "User[ip_address]": fakeIp,
            "User[status_id]": 1,
            "User[user_referral_code]": "",
            "User[send_sms]": 1,
            "User[reCaptcha]": "",
            "g-recaptcha-response": "",
        }

        raw_body = urlencode(payload)

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": BASE_URL,
            "referer": SIGNUP_URL,
            "x-csrf-token": csrf,
            "x-requested-with": "XMLHttpRequest",
        }

        # 4️⃣ POST signup
        r = session.post(
            SIGNUP_URL,
            headers=headers,
            data=raw_body,
            timeout=15,
        )

        success, msg = is_signup_success(r)

        if success:
            logger.info(f"[INFO] Account {username} created")
            logger.info(f"[INFO] Password: {password}")
            state.INGAME_STATE.setUsername(username)
            state.INGAME_STATE.setPassword(password)
            log_username(username)

            if get_auto_email_verification() or get_auto_mobile_verification():
                start_account_verification_async(username)

            return True, msg
        else:
            logger.info(f"[ERROR] Failed to create account {username}: due to username existed or duplicated email used.")
            #logger.info(f"[DEBUG] Raw response: {r.text}")
            return False, msg       

    except (ConnectionError, Timeout, RemoteDisconnected) as e:
        logger.warning(f"[NET] Signup dropped by server: {e}")
        return False, "connection_dropped"
    
    except RequestException as e:
        logger.error(f"[NETWORK_ERROR] Signup dropped by server: {e}")
        return False, "Network error (DNS / connection failed)"

    except Exception as e:
        logger.exception("[FATAL] Unexpected signup error")
        return False, str(e)

# ============================================================
# TKINTER UI
# ============================================================

def generate_username(prefix="", postfix=""):
    prefix = str(prefix).strip().lower()
    postfix = str(postfix).strip().lower()

    has_prefix = bool(prefix)
    has_postfix = bool(postfix)

    underscore_count = (1 if has_prefix else 0) + (1 if has_postfix else 0)
    fixed_length = len(prefix) + len(postfix) + underscore_count

    target_length = random.randint(
        max(MIN_USERNAME_LENGTH, fixed_length + 1),
        MAX_USERNAME_LENGTH
    )

    remaining = max(1, target_length - fixed_length)

    random_part = generate_random_string(remaining, remaining)

    if has_prefix and has_postfix:
        return f"{prefix}{random_part}{postfix}"
    elif has_prefix:
        return f"{prefix}{random_part}"
    elif has_postfix:
        return f"{random_part}{postfix}"
    else:
        return random_part


def generate_email(prefix="", postfix="", domain="mail.com", length=12):
    prefix = str(prefix).strip().lower()
    postfix = str(postfix).strip().lower()

    rand = generate_random_string(length, length)
    local = "".join(p for p in [prefix, rand, postfix] if p)

    return f"{local}@{domain}"



# ============================================================
# UI CALLBACKS
# ============================================================

def schedule_auto_start_endless():
    global auto_start_timer_id

    # Avoid double scheduling
    if auto_start_timer_id is not None:
        return

    logger.info("[INFO] Auto-start Endless Mode scheduled in 5 seconds")

    auto_start_timer_id = root.after(
        AUTO_START_DELAY_MS,
        execute_auto_start_endless
    )


def cancel_auto_start_endless():
    global auto_start_timer_id

    if auto_start_timer_id is not None:
        root.after_cancel(auto_start_timer_id)
        auto_start_timer_id = None
        logger.info("[INFO] Auto-start Endless Mode cancelled")


def execute_auto_start_endless():
    global auto_start_timer_id
    auto_start_timer_id = None

    # Final guard: user might untick at the last moment
    if auto_start_endless_var.get():
        logger.info("[INFO] Auto-starting Endless Mode now")
        on_start_endless_mode()
    else:
        logger.info("[INFO] Auto-start aborted (checkbox unchecked)")

def resetState():
    state.STOP_EVENT.clear()
    state.CRASH_EVENT.clear()

def run_rageborn_flow(username, password):
    try:
        if not launch_game_process():
            logger.error("[ERROR] Game launch aborted")
            return
        
        if state.SLOWER_PC_MODE:
            logger.info("[INFO] RAGEBORN slow mode activated.")

        import rageborn

        resetState()
        rageborn.start(username, password)

        if state.CRASH_EVENT.is_set():
            logger.exception("[FATAL] Rageborn crashed during runtime")
            raise

    except RuntimeError:
        raise
    except Exception:
        logger.exception("[FATAL] Rageborn crashed")
        raise
    except pyautogui.FailSafeException:
        logger.info("[SAFETY] FAILSAFE Triggered! Emergency stop.")
        state.STOP_EVENT.set()
        raise

    finally:
        kill_jokevio()
        logger.info("[MAIN] Rageborn thread exited")


def run_rageborn_flow_thread(username, password):
    try:
        run_rageborn_flow(username, password)
    except RuntimeError as e:
        logger.error(f"[THREAD-CRASH] {e}")
    except Exception:
        logger.exception("[THREAD-CRASH] Unexpected error")


def start_rageborn_async(username, password):    
    t = threading.Thread(
        target=run_rageborn_flow_thread,
        args=(username, password),
        daemon=True
    )
    t.start()

# ----------------- UI callbacks -----------------
def get_effective_password():
    pwd = password_entry.get().strip()
    return pwd if pwd else DEFAULT_PASSWORD


def log_username(username, filename="signup_users.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(username + "\n")

def on_generate():
    prefix = prefix_entry.get().strip()
    postfix = postfix_entry.get().strip()
    domain = domain_entry.get().strip() or "mail.com"

    username = generate_word_username(
        prefix=prefix,
        postfix=postfix
    )

    email = generate_email(prefix, postfix, domain)

    username_entry.delete(0, tk.END)
    username_entry.insert(0, username)

    email_entry.delete(0, tk.END)
    email_entry.insert(0, email)

def kill_jokevio():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "juvio.exe"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"[INFO] Jokevio.exe killed")
    except subprocess.CalledProcessError:
        logger.info(f"[INFO] Intend to kill Jokevio.exe, but its not running")

# ============================================================
# UI Application 
# ============================================================
root = tk.Tk()
root.update_idletasks()  # ensure geometry info is ready
root.title(f"{INFO_NAME} v{VERSION}")

auto_mode_var = tk.BooleanVar(value=False)
duration_var = tk.StringVar(value="Duration: 00:00:00")
iteration_var = tk.StringVar(value="Iterations completed: 0")
auto_start_endless_var = tk.BooleanVar(value=get_auto_start_endless())
auto_start_countdown_var = tk.StringVar(value="")
auto_email_verification_var = tk.BooleanVar(
    value=get_auto_email_verification()
)
auto_mobile_verification_var = tk.BooleanVar(
    value=get_auto_mobile_verification()
)
auto_update_var = tk.BooleanVar(value=read_auto_update())
auto_restart_dns_var = tk.BooleanVar(value=get_auto_restart_dns())
settings_for_slower_pc_var = tk.BooleanVar(value=get_settings_for_slower_pc())

def one_full_cycle():
    try:
        while True:
            # 1️⃣ Generate username/email
            on_generate()

            # 2️⃣ Read generated credentials
            username = username_entry.get()
            password = get_effective_password()

            logger.info("-------------------------------------------")
            logger.info(f"[INFO] Generated account: {username}")

            # 3️⃣ Run signup
            try:
                success, msg = signup_user(
                    first_name_entry.get(),
                    last_name_entry.get(),
                    email_entry.get(),
                    username,
                    password
                )
            except Exception as e:
                logger.warning(f"[WARN] Signup exception, regenerating: {e}")
                success = False
                msg = "exception"
            
            if success:
                break
            
            logger.info(f"[INFO] Failed to signup account {username}: {msg}")
            logger.info("[INFO] Regenerating new account")
            time.sleep(random.uniform(8, 15))

        logger.info(f"[INFO] Signup success! ")
        logger.info(f"Username {username} launching Rageborn.exe")

        # 4️⃣ Run rageborn (blocking inside worker thread)
        run_rageborn_flow(username, password)

        return True
    except Exception:
        logger.exception("[WARN] Cycle error, recovering")
        time.sleep(10)
        raise

def auto_loop_worker():
    logger.info(f"[INFO] --Endless mode started--v{VERSION}")

    root.after(0, set_start_time)

    global iteration_count
    iteration_count = 0
    root.after(0, lambda: iteration_var.set("Iterations completed: 0"))

    while auto_mode_var.get():
        try:
            one_full_cycle()

            root.after(0, increment_iteration)

        except Exception as e:
            # ABSOLUTE LAST LINE OF DEFENSE
            logger.exception("[FATAL] Cycle crashed, recovering")

            # Cooldown to avoid rapid crash loops
            time.sleep(10)

            # Continue forever
            continue

    logger.info("[INFO] Endless mode stopped")

def set_start_time():
    global auto_start_time
    auto_start_time = datetime.now()
    duration_var.set("Duration: 00:00:00")
    
def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def increment_iteration():
    global iteration_count, auto_start_time

    iteration_count += 1
    iteration_var.set(f"Iterations completed: {iteration_count}")

    if auto_start_time:
        elapsed = int((datetime.now() - auto_start_time).total_seconds())
        duration_var.set(f"Duration: {format_duration(elapsed)}")

def poll_log_queue():
    while not log_queue.empty():
        record = log_queue.get()

        # 1️⃣ Convert LogRecord → string
        msg = ui_formatter.format(record)

        log_text.config(state="normal")

        # ---- LOG LEVEL DETECTION ----
        tag = "INFO"

        if (
            "[FATAL]" in msg
            or "Traceback" in msg
            or "RuntimeError" in msg
            or "Exception" in msg
            or record.levelname in ("ERROR", "CRITICAL")
        ):
            tag = "ERROR"
        elif record.levelname == "WARNING" or "[WARN]" in msg:
            tag = "WARN"

        # 2️⃣ Insert formatted string
        log_text.insert("end", msg + "\n", tag)
        log_text.see("end")
        log_text.config(state="disabled")

    root.after(100, poll_log_queue)


def on_login_only():
    user = username_entry.get().strip()
    pwd = get_effective_password()

    if not user or not pwd:
        messagebox.showerror("Error", "Username and password are required")
        return

    logger.info(f"[INFO] Logging in with existing account: {user}")
    start_rageborn_async(user, pwd)

def on_signup_only():
    """Sign up ONLY, no Rageborn"""
    on_submit()

def on_signup_and_run_once():
    """Sign up, then run Rageborn once"""
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = get_effective_password()

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_user(first, last, email, user, pwd)

    if success:
        start_rageborn_async(user, pwd)
    else:
        messagebox.showerror("Failed", msg)


def on_start_endless_mode():
    """Start endless mode (replaces checkbox)"""
    if not auto_mode_var.get():
        auto_mode_var.set(True)

        root.after(0, set_endless_mode_ui_running)

        threading.Thread(
            target=auto_loop_worker,
            daemon=True
        ).start()

def on_submit():
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = get_effective_password()

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_user(first, last, email, user, pwd)

    if success:
        logger.info("[INFO] Signup successful!")
    else:
        logger.error(f"[ERROR] Signup failed: {msg}")

def on_browse_executable():
    exe_path = filedialog.askopenfilename(
        title="Select Juvio Game Executable",
        filetypes=[("Executable files", "*.exe")]
    )

    if not exe_path:
        return  # user cancelled

    filename = os.path.basename(exe_path).lower()

    if filename != "juvio.exe":
        messagebox.showerror(
            "Invalid Game Launcher",
            "Invalid executable selected.\n\n"
            "Please select:\n"
            "juvio.exe"
        )
        return

    if not os.path.isfile(exe_path):
        messagebox.showerror("Error", "Selected file does not exist")
        return

    game_exe_var.set(exe_path)
    set_game_executable(exe_path)

    logger.info(f"[INFO] Game executable set: {exe_path}")
    exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))



def launch_game_process():
    exe = game_exe_var.get()

    if not exe:
        messagebox.showerror(
            "Error",
            "Please select game launcher first."
        )
        return False

    if not os.path.isfile(exe):
        messagebox.showerror(
            "Executable missing",
            "The selected executable no longer exists."
        )
        return False

    if os.path.basename(exe).lower() != "juvio.exe":
        messagebox.showerror(
            "Invalid Game Launcher",
            "Configured executable is not juvio.exe.\n"
            "Please re-select the correct file."
        )
        return False
    
    # Prepare startup.cfg
    prepare_game_config(
        logger=logger,
        window_mode=2,
        width=1024,
        height=768
    )

    subprocess.Popen(
        [exe],
        cwd=os.path.dirname(exe)
    )
    return True


def validate_game_executable(show_error=True):
    exe = game_exe_var.get()

    if not exe:
        if show_error:
            messagebox.showerror(
                "Error",
                "Please select game launcher first."
            )
        return False

    if not os.path.isfile(exe):
        if show_error:
            messagebox.showerror(
                "Executable missing",
                "The selected executable no longer exists."
            )
        return False

    if os.path.basename(exe).lower() != "juvio.exe":
        if show_error:
            messagebox.showerror(
                "Invalid Game Launcher",
                "Configured executable is not juvio.exe."
            )
        return False

    return True

def on_auto_start_checkbox_changed():    
    value = auto_start_endless_var.get()
    set_auto_start_endless(value)

    if value:
        # ✅ validate only (DO NOT LAUNCH)
        if not validate_game_executable():
            auto_start_endless_var.set(False)
            set_auto_start_endless(False)
            cancel_auto_start_endless()
            logger.error("[ERROR] Invalid game executable, auto-start cancelled")
            return

        # ✅ only schedule countdown
        schedule_auto_start_endless()

    else:
        cancel_auto_start_endless()


def try_auto_start_from_config():
    """
    Called on app startup when auto_start=true in config.
    Must validate executable before scheduling countdown.
    """
    if not auto_start_endless_var.get():
        return

    if not validate_game_executable(show_error=False):
        logger.error(
            "[ERROR] Auto-start enabled in config, but game executable is invalid. Auto-start disabled."
        )

        auto_start_endless_var.set(False)
        set_auto_start_endless(False)
        auto_start_countdown_var.set("")
        return

    schedule_auto_start_endless()



def update_auto_start_countdown():
    global auto_start_remaining, auto_start_countdown_id

    if auto_start_remaining <= 0:
        auto_start_countdown_var.set("")
        auto_start_countdown_id = None
        execute_auto_start_endless()
        return

    auto_start_countdown_var.set(
        f"Auto start in {auto_start_remaining}…"
    )
    auto_start_remaining -= 1

    auto_start_countdown_id = root.after(1000, update_auto_start_countdown)


def schedule_auto_start_endless():    
    global auto_start_timer_id, auto_start_remaining

    if auto_start_timer_id is not None:
        return  # already scheduled

    auto_start_remaining = AUTO_START_DELAY_SECONDS
    auto_start_countdown_var.set(
        f"Auto start in {auto_start_remaining}…"
    )

    logger.info("[INFO] Auto-start Endless Mode scheduled")

    auto_start_timer_id = True  # logical flag
    update_auto_start_countdown()


def cancel_auto_start_endless():
    global auto_start_timer_id, auto_start_countdown_id

    if auto_start_countdown_id is not None:
        root.after_cancel(auto_start_countdown_id)
        auto_start_countdown_id = None

    auto_start_timer_id = None
    auto_start_countdown_var.set("")

    logger.info("[INFO] Auto-start Endless Mode cancelled")


def execute_auto_start_endless():
    global auto_start_timer_id

    auto_start_timer_id = None

    if auto_start_endless_var.get():
        logger.info("[INFO] Auto-starting Endless Mode now")
        root.after(0, set_endless_mode_ui_running)
        on_start_endless_mode()
    else:
        logger.info("[INFO] Auto-start aborted (checkbox unchecked)")


def labeled_entry(parent, label, default=""):
    tk.Label(parent, text=label, anchor="w").pack(fill="x")
    e = tk.Entry(parent)
    e.pack(fill="x", pady=2)
    if default:
        e.insert(0, default)
    return e

def set_endless_mode_ui_running():
    start_endless_btn.config(
        text="Hit F11 to stop",
        fg="red",
        state="disabled"
    )

def set_endless_mode_ui_idle():
    start_endless_btn.config(
        text="Start Endless Mode",
        fg="black",
        state="normal"
    )

def on_auto_email_verification_changed():
    set_auto_email_verification(
        auto_email_verification_var.get()
    )

def on_auto_mobile_verification_changed():
    set_auto_mobile_verification(
        auto_mobile_verification_var.get()
    )

def on_auto_update_changed():
    set_auto_update(
        auto_update_var.get()
    )


WINDOW_WIDTH = 750
WINDOW_HEIGHT = 800

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = screen_width - 10 - WINDOW_WIDTH
y = screen_height - 90 - WINDOW_HEIGHT

root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

left_frame = tk.Frame(main_frame)
left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
left_frame.rowconfigure(0, weight=1)

form_frame = tk.Frame(left_frame)
form_frame.pack(fill="x", anchor="n")

spacer = tk.Frame(left_frame)
spacer.pack(fill="both", expand=True)

main_frame.columnconfigure(0, weight=0)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(0, weight=1)

first_name_entry = labeled_entry(form_frame, "First Name", DEFAULT_FIRST_NAME)
last_name_entry = labeled_entry(form_frame, "Last Name", DEFAULT_LAST_NAME)
prefix_entry = labeled_entry(form_frame, "Prefix (optional)")
postfix_entry = labeled_entry(form_frame, "Postfix (optional)")
domain_entry = labeled_entry(form_frame, "Email Domain", "mail.com")
email_entry = labeled_entry(form_frame, "Email")
username_entry = labeled_entry(form_frame, "Username")
password_entry = labeled_entry(form_frame, "Password", DEFAULT_PASSWORD)

game_exe_var = tk.StringVar(value=get_game_executable())
exe_header = tk.Frame(form_frame)
exe_header.pack(fill="x", pady=(8, 0))

tk.Label(
    exe_header,
    text="Game Launcher"
).pack(side="left")

tk.Button(
    exe_header,
    text="Browse",
    command=on_browse_executable,
    width=10
).pack(side="right")

exe_entry = tk.Entry(
    form_frame,
    textvariable=game_exe_var,
    state="readonly"
)
exe_entry.pack(fill="x", pady=(4, 0))

tk.Button(
    form_frame,
    text="Generate Username & Email",
    command=on_generate
).pack(fill="x", pady=6)

action_row = tk.Frame(form_frame)
action_row.pack(fill="x", pady=6)

tk.Button(
    action_row,
    text="Sign Up",
    command=on_submit,
    width=12
).pack(side="left", expand=True, padx=2)

tk.Button(
    action_row,
    text="Login",
    command=on_login_only,
    width=12
).pack(side="left", expand=True, padx=2)

tk.Button(
    form_frame,
    text="Sign up and run once",
    command=on_signup_and_run_once
).pack(fill="x", pady=4)

status_frame = tk.LabelFrame(left_frame, text="Endless Mode Status")
status_frame.pack(fill="x", side="bottom", pady=10)

tk.Checkbutton(
    status_frame,
    text="Auto start Endless Mode on launch",
    variable=auto_start_endless_var,
    command=on_auto_start_checkbox_changed
).pack(anchor="w", pady=(2, 4))

countdown_label = tk.Label(
    status_frame,
    textvariable=auto_start_countdown_var,
    fg="orange"
)
countdown_label.pack(anchor="w")

duration_label = tk.Label(status_frame, textvariable=duration_var)
duration_label.pack(anchor="w")

iteration_label = tk.Label(status_frame, textvariable=iteration_var)
iteration_label.pack(anchor="w")

start_endless_btn = tk.Button(
    status_frame,
    text="Start Endless Mode",
    command=on_start_endless_mode,
    fg="black"
)
start_endless_btn.pack(fill="x", pady=6)


right_frame = tk.Frame(main_frame)
right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

notebook = ttk.Notebook(right_frame)
notebook.pack(fill="both", expand=True)

extra_settings_tab = tk.Frame(notebook)
logs_tab = tk.Frame(notebook)

notebook.add(extra_settings_tab, text="Extra Settings")
account_verification_frame = tk.LabelFrame(
    extra_settings_tab,
    text="Account Verification Settings",
    padx=10,
    pady=8
)
account_verification_frame.pack(
    fill="x",
    padx=10,
    pady=10,
    anchor="n"
)

verification_row = tk.Frame(account_verification_frame)
verification_row.pack(anchor="w", pady=4)

tk.Checkbutton(
    verification_row,
    text="Auto Email Verification",
    variable=auto_email_verification_var,
    command=on_auto_email_verification_changed
).grid(row=0, column=0, sticky="w", padx=(0, 20))

tk.Checkbutton(
    verification_row,
    text="Auto Mobile Verification",
    variable=auto_mobile_verification_var,
    command=on_auto_mobile_verification_changed
).grid(row=0, column=1, sticky="w")

app_settings_frame = tk.LabelFrame(
    extra_settings_tab,
    text="Application Settings",
    padx=10,
    pady=8
)
app_settings_frame.pack(
    fill="x",
    padx=10,
    pady=10,
    anchor="n"
)

app_settings_row = tk.Frame(app_settings_frame)
app_settings_row.pack(anchor="w", pady=4)

tk.Checkbutton(
    app_settings_row,
    text="Auto Updates",
    variable=auto_update_var,
    command=on_auto_update_changed
).grid(row=0, column=0, sticky="w", padx=(0, 20))

tk.Checkbutton(
    app_settings_row,
    text="Auto Restart PC on DNS Failure",
    variable=auto_restart_dns_var,
    command=lambda: set_auto_restart_dns(auto_restart_dns_var.get())
).grid(row=0, column=1, sticky="w")

app_settings_row2 = tk.Frame(app_settings_frame)
app_settings_row2.pack(anchor="w", pady=4)

tk.Checkbutton(
    app_settings_row2,
    text="Settings for Slower PC",
    variable=settings_for_slower_pc_var,
    command=lambda: set_settings_for_slower_pc(settings_for_slower_pc_var.get())
).grid(row=0, column=0, sticky="w", padx=(0, 20))

notebook.add(logs_tab, text="Logs")

log_text = tk.Text(
    logs_tab,
    bg="black",
    fg="lime",
    font=("Consolas", 9),
    state="disabled"
)
log_text.pack(fill="both", expand=True)

log_text.tag_configure("INFO", foreground="lime")
log_text.tag_configure("WARN", foreground="orange")
log_text.tag_configure("ERROR", foreground="red")

notebook.select(logs_tab)

style = ttk.Style()
style.theme_use("default")

poll_log_queue()
exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))

# ============================================================
# AUTO START ENDLESS MODE (DELAYED & CANCELLABLE)
# ============================================================

if auto_start_endless_var.get():
    try_auto_start_from_config()

if __name__ == "__main__":
    set_self_high_priority()
    root.mainloop()