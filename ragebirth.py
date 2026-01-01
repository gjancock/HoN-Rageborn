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
from utilities.usernameGenerator import generate_word_username, generate_random_string
from requests.exceptions import ConnectionError, Timeout
from http.client import RemoteDisconnected
import configparser
import pyautogui
from utilities.common import resource_path
import pytesseract
from utilities.ocrConfig import ensure_tesseract_configured, get_config

# Logger
log_queue = Queue()
logger = setup_logger(ui_queue=log_queue)

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


# ============================================================
# APPLICATION SETTINGS
# ============================================================
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
        path = resource_path("VERSION")
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

CONFIG_FILE = os.path.join(get_runtime_dir(), "rageborn.ini")

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

def get_auto_start_endless():
    config = load_config()
    return config.getboolean("endless", "auto_start", fallback=False)

def set_auto_start_endless(value: bool):
    config = load_config()
    if "endless" not in config:
        config["endless"] = {}
    config["endless"]["auto_start"] = "true" if value else "false"
    save_config(config)


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
        resp = session.get(SIGNUP_URL, timeout=15)
        resp.raise_for_status()

        match = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
        if not match:
            logger.error("[ERROR] Failed to get CSRF token.")
            return False, "CSRF not found"

        csrf = match.group(1)

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
            "User[ip_address]": "127.0.0.1",
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
            log_username(username)
            return True, msg
        else:
            logger.info(f"[ERROR] Failed to create account {username}: due to username existed or duplicated email used.")
            #logger.info(f"[DEBUG] Raw response: {r.text}")
            return False, msg       

    except (ConnectionError, Timeout, RemoteDisconnected) as e:
        logger.warning(f"[NET] Signup dropped by server: {e}")
        return False, "connection_dropped"

    except Exception as e:
        logger.exception("[FATAL] Unexpected signup error")
        return False, str(e)

# ============================================================
# TKINTER UI
# ============================================================

def generate_username(prefix="", postfix=""):
    prefix = prefix.strip()
    postfix = postfix.strip()

    has_prefix = bool(prefix)
    has_postfix = bool(postfix)

    underscore_count = (1 if has_prefix else 0) + (1 if has_postfix else 0)
    fixed_length = len(prefix) + len(postfix) + underscore_count

    target_length = random.randint(
        max(MIN_USERNAME_LENGTH, fixed_length + 1),
        MAX_USERNAME_LENGTH
    )

    remaining = target_length - fixed_length
    if remaining < 1:
        remaining = 1

    random_part = generate_random_string(remaining)

    if has_prefix and has_postfix:
        return f"{prefix}_{random_part}_{postfix}"
    elif has_prefix:
        return f"{prefix}_{random_part}"
    elif has_postfix:
        return f"{random_part}_{postfix}"
    else:
        return random_part

def generate_email(prefix="", postfix="", domain="mail.com", length=6):
    rand = generate_random_string(length)
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

def run_rageborn_flow(username, password):
    try:
        ensure_tesseract_configured()
        import rageborn

        resetState()
        rageborn.start(username, password)

    except Exception:
        logger.exception("[FATAL] Rageborn crashed")
    except pyautogui.FailSafeException:
        logger.info("[SAFETY] FAILSAFE Triggered! Emergency stop.")
        state.STOP_EVENT.set()

    finally:
        kill_jokevio()
        logger.info("[MAIN] Rageborn thread exited")

def start_rageborn_async(username, password):    
    t = threading.Thread(
        target=run_rageborn_flow,
        args=(username, password),
        daemon=True
    )
    t.start()

# ----------------- UI callbacks -----------------
def get_effective_password():
    pwd = password_entry.get().strip()
    return pwd if pwd else DEFAULT_PASSWORD

def on_signup_success():
    username = username_entry.get()
    password = get_effective_password()

    start_rageborn_async(username, password)

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

        logger.info(f"[INFO] Signup success! Username {username} ..launching Rageborn.exe")

        # 4️⃣ Run rageborn (blocking inside worker thread)
        run_rageborn_flow(username, password)

        return True
    except Exception:
        logger.exception("[WARN] Cycle error, recovering")
        time.sleep(10)

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
        msg = log_queue.get()

        log_text.config(state="normal")

        # ---- LOG LEVEL DETECTION ----
        tag = "INFO"

        if (
            "[FATAL]" in msg
            or "Traceback" in msg
            or "RuntimeError" in msg
            or "Exception" in msg
        ):
            tag = "ERROR"
        elif "[WARN]" in msg:
            tag = "WARN"

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
        messagebox.showinfo("Success", "Signup successful!")
    else:
        messagebox.showerror("Failed", msg)

def ocr_self_test():
    ensure_tesseract_configured()

    import numpy as np

    img = np.zeros((60, 200), dtype=np.uint8)
    cv2 = __import__("cv2")
    cv2.putText(
        img,
        "TEST123",
        (5, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        255,
        2
    )

    cfg = get_config()
    logger.info(f"[OCR DEBUG] OCR config = {cfg}")

    text = pytesseract.image_to_string(img, config=get_config()).strip()
    return text

def on_test_ocr():
    try:
        result = ocr_self_test()

        if result:
            logger.info(f"[OCR TEST] Success: '{result}'")
            messagebox.showinfo(
                "OCR Test",
                f"OCR succeeded!\n\nResult:\n{result}"
            )
        else:
            logger.warning("[OCR TEST] OCR ran but returned empty text")
            messagebox.showwarning(
                "OCR Test",
                "OCR ran, but returned empty text.\n"
                "Check tessdata / whitelist / config."
            )

    except Exception as e:
        logger.error(f"[OCR TEST] Failed: {e}")
        messagebox.showerror(
            "OCR Test Failed",
            f"OCR test failed:\n\n{e}"
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

right_frame = tk.Frame(main_frame)
right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

main_frame.columnconfigure(0, weight=0)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(0, weight=1)

def labeled_entry(parent, label, default=""):
    tk.Label(parent, text=label, anchor="w").pack(fill="x")
    e = tk.Entry(parent)
    e.pack(fill="x", pady=2)
    if default:
        e.insert(0, default)
    return e

first_name_entry = labeled_entry(form_frame, "First Name", DEFAULT_FIRST_NAME)
last_name_entry = labeled_entry(form_frame, "Last Name", DEFAULT_LAST_NAME)
prefix_entry = labeled_entry(form_frame, "Prefix (optional)")
postfix_entry = labeled_entry(form_frame, "Postfix (optional)")
domain_entry = labeled_entry(form_frame, "Email Domain", "mail.com")
email_entry = labeled_entry(form_frame, "Email")
username_entry = labeled_entry(form_frame, "Username")
password_entry = labeled_entry(form_frame, "Password", DEFAULT_PASSWORD)

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

tk.Button(
    form_frame,
    text="Test OCR",
    command=on_test_ocr,
    fg="blue"
).pack(fill="x", pady=(0, 8))


status_frame = tk.LabelFrame(left_frame, text="Endless Mode Status")
status_frame.pack(fill="x", side="bottom", pady=10)

def on_auto_start_checkbox_changed():
    value = auto_start_endless_var.get()
    set_auto_start_endless(value)

    if value:
        schedule_auto_start_endless()
    else:
        cancel_auto_start_endless()

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
        on_start_endless_mode()
    else:
        logger.info("[INFO] Auto-start aborted (checkbox unchecked)")


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

tk.Button(
    status_frame,
    text="Start Endless Mode",
    command=on_start_endless_mode,
    fg="red"
).pack(fill="x", pady=6)

log_text = tk.Text(
    right_frame,
    bg="black",
    fg="lime",
    font=("Consolas", 9),
    state="disabled"
)
log_text.pack(fill="both", expand=True)
log_text.tag_configure("INFO", foreground="lime")
log_text.tag_configure("WARN", foreground="orange")
log_text.tag_configure("ERROR", foreground="red")

poll_log_queue()

# ============================================================
# AUTO START ENDLESS MODE (DELAYED & CANCELLABLE)
# ============================================================

if auto_start_endless_var.get():
    schedule_auto_start_endless()


if __name__ == "__main__":
    root.mainloop()