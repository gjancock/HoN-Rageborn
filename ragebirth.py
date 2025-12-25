import tkinter as tk
from tkinter import messagebox
import requests
import re
from urllib.parse import urlencode
import random
import string
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

# ============================================================
# APPLICATION SETTINGS
# ============================================================
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def read_version():
    try:
        path = resource_path("VERSION")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        logger.error("[INFO_ERROR] Unable to find VERSION")
        return "unknown"
    
#
INFO_NAME = "Rageborn"
VERSION = read_version()

# ============================================================
# SIGNUP LOGIC (NO UI CODE HERE)
# ============================================================

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
            logger.error("[INFO_ERROR] Failed to get CSRF token.")
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

        if r.status_code == 200:
            logger.info(f"[INFO] Account {username} created, password: {password}")
            log_username(username)
            return True, "Signup Successfully"

        return False, f"HTTP {r.status_code}"

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

def resetState():
    state.STOP_EVENT.clear()

def run_rageborn_flow(username, password):
    import rageborn

    resetState()
    rageborn.start(username, password)

    # after rageborn finishes
    kill_jokevio()

def start_rageborn_async(username, password):    
    threading.Thread(
        target=run_rageborn_flow,
        args=(username, password),
        daemon=True
    ).start()

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
# AUTOMATION
# ============================================================
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
    logger.info("[INFO] Endless mode started")

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

def on_auto_toggle():
    if auto_mode_var.get():
        threading.Thread(
            target=auto_loop_worker,
            daemon=True
        ).start()
    else:
        duration_var.set("Duration: 00:00:00")

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

# ============================================================
# TKINTER UI
# ============================================================

def poll_log_queue():
    while not log_queue.empty():
        msg = log_queue.get()
        log_text.config(state="normal")
        log_text.insert("end", msg + "\n")
        log_text.see("end")
        log_text.config(state="disabled")

    root.after(100, poll_log_queue)

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
        on_signup_success()
    else:
        messagebox.showerror("Failed", msg)

root = tk.Tk()
root.update_idletasks()  # ensure geometry info is ready
root.title(f"{INFO_NAME} v{VERSION}")

WINDOW_WIDTH = 425
WINDOW_HEIGHT = 590

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = screen_width - 10 - WINDOW_WIDTH
y = screen_height - 90 - WINDOW_HEIGHT

root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

tk.Label(root, text="Password").pack()
password_entry = tk.Entry(root)
password_entry.pack()

tk.Label(root, text="First Name").pack()
first_name_entry = tk.Entry(root)
first_name_entry.pack()

tk.Label(root, text="Last Name").pack()
last_name_entry = tk.Entry(root)
last_name_entry.pack()

tk.Label(root, text="Prefix (optional)").pack()
prefix_entry = tk.Entry(root)
prefix_entry.pack()

tk.Label(root, text="Postfix (optional)").pack()
postfix_entry = tk.Entry(root)
postfix_entry.pack()

tk.Label(root, text="Email Domain").pack()
domain_entry = tk.Entry(root)
domain_entry.insert(0, "mail.com")
domain_entry.pack()

tk.Button(root, text="Generate Username & Email", command=on_generate).pack(pady=10)

tk.Label(root, text="Username").pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Email").pack()
email_entry = tk.Entry(root)
email_entry.pack()

auto_mode_var = tk.BooleanVar(value=False)

auto_mode_checkbox = tk.Checkbutton(
    root,
    text="Auto Generate & Run",
    variable=auto_mode_var
)
auto_mode_checkbox.pack(pady=5)

auto_mode_checkbox.config(command=on_auto_toggle)

duration_var = tk.StringVar(value="Duration: 00:00:00")
duration_label = tk.Label(root, textvariable=duration_var)
duration_label.pack(pady=2)

iteration_var = tk.StringVar(value="Iterations completed: 0")

iteration_label = tk.Label(root, textvariable=iteration_var)
iteration_label.pack(pady=2)

tk.Button(root, text="Sign Up", command=on_submit).pack(pady=10)

log_text = tk.Text(
    root,
    height=20,
    width=100,
    state="disabled",
    bg="black",
    fg="lime",
    font=("Consolas", 9)
)
log_text.pack(fill="both", expand=True, padx=5, pady=5)

#
first_name_entry.insert(0, DEFAULT_FIRST_NAME)
last_name_entry.insert(0, DEFAULT_LAST_NAME)
password_entry.insert(0, DEFAULT_PASSWORD)

poll_log_queue()

if __name__ == "__main__":
    root.mainloop()