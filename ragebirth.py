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

    # 1️⃣ GET signup page
    resp = session.get(SIGNUP_URL, timeout=15)
    resp.raise_for_status()

    # 2️⃣ Extract CSRF
    match = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
    if not match:
        return False, "Failed to get CSRF token"

    csrf = match.group(1)

    # 3️⃣ Build payload
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
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
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
        log_username(username) # Save username to textfile
        return True, "Signup successful!"
    else:
        return False, r.text


# ============================================================
# TKINTER UI
# ============================================================

def generate_random_string(length):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_username(prefix="", postfix=""):
    """
    Username rules:
    - total length randomly chosen between 2 and 16
    - supports prefix & postfix
    - random part is alphanumeric
    """

    prefix = prefix.strip().lower()
    postfix = postfix.strip().lower()

    has_prefix = bool(prefix)
    has_postfix = bool(postfix)

    # underscores count
    underscore_count = (1 if has_prefix else 0) + (1 if has_postfix else 0)
    if has_prefix and has_postfix:
        underscore_count = 2

    fixed_length = len(prefix) + len(postfix) + underscore_count

    # Pick a random TOTAL length
    target_length = random.randint(
        max(MIN_USERNAME_LENGTH, fixed_length + 1),
        MAX_USERNAME_LENGTH
    )

    remaining = target_length - fixed_length

    if remaining < 1:
        # fallback if prefix/postfix too long
        base = (prefix + postfix)[:MAX_USERNAME_LENGTH]
        if len(base) < MIN_USERNAME_LENGTH:
            base += generate_random_string(MIN_USERNAME_LENGTH - len(base))
        return base

    random_part = generate_random_string(remaining)

    if has_prefix and has_postfix:
        return f"{prefix}{random_part}{postfix}"
    elif has_prefix:
        return f"{prefix}{random_part}"
    elif has_postfix:
        return f"{random_part}{postfix}"
    else:
        return random_part

def generate_email(prefix="", postfix="", domain="mail.com", length=6):
    rand = generate_random_string(length)
    local = "".join(p for p in [prefix, rand, postfix] if p)
    return f"{local}@{domain}"


# ============================================================
# UI CALLBACKS
# ============================================================

def run_rageborn_flow(username, password):
    import rageborn
    rageborn.main(username, password)

    # after rageborn finishes
    kill_jokevio()
    show_root()

def start_rageborn_async(username, password):
    hide_root()
    threading.Thread(
        target=run_rageborn_flow,
        args=(username, password),
        daemon=True
    ).start()

# ----------------- UI callbacks -----------------

def on_signup_success():
    username = username_entry.get()
    password = password_entry.get()

    start_rageborn_async(username, password)

def log_username(username, filename="signup_users.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(username + "\n")

def on_generate():
    prefix = prefix_entry.get().strip()
    postfix = postfix_entry.get().strip()
    domain = domain_entry.get().strip() or "mail.com"

    username = generate_username(prefix, postfix)
    email = generate_email(prefix, postfix, domain)

    username_entry.delete(0, tk.END)
    username_entry.insert(0, username)

    email_entry.delete(0, tk.END)
    email_entry.insert(0, email)

def hide_root():
    root.withdraw()   # hide window

def show_root():
    root.deiconify()  # show window again

def kill_jokevio():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "juvio.exe"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("jokevio.exe killed")
    except subprocess.CalledProcessError:
        print("jokevio.exe not running")

# ============================================================
# AUTOMATION
# ============================================================
def one_full_cycle():
    # 1️⃣ Generate username/email
    on_generate()   # reuse your existing Generate button logic

    # 2️⃣ Read generated credentials
    username = username_entry.get()
    password = password_entry.get()

    print(f"[AUTO] Generated account: {username}")

    # 3️⃣ Run signup
    success, msg = signup_user(
        first_name_entry.get(),
        last_name_entry.get(),
        email_entry.get(),
        username,
        password
    )

    if not success:
        print("[AUTO] Signup failed:", msg)
        return False

    print("[AUTO] Signup success, starting rageborn")

    # 4️⃣ Run rageborn (blocking inside worker thread)
    run_rageborn_flow(username, password)

    return True

def auto_loop_worker():
    print("[AUTO] Auto mode started")

    while auto_mode_var.get():
        ok = one_full_cycle()

        if not ok:
            print("[AUTO] Cycle failed, retrying...")
            time.sleep(2)
            continue

        print("[AUTO] Cycle complete, next iteration...")
        time.sleep(1)

    print("[AUTO] Auto mode stopped")

def on_auto_toggle():
    if auto_mode_var.get():
        threading.Thread(
            target=auto_loop_worker,
            daemon=True
        ).start()

# ============================================================
# TKINTER UI
# ============================================================

def on_submit():
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = password_entry.get()

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_user(first, last, email, user, pwd)

    if success:
        #messagebox.showinfo("Success", msg)        
        on_signup_success()
    else:
        messagebox.showerror("Failed", msg)

root = tk.Tk()
root.update_idletasks()  # ensure geometry info is ready
root.title("Random Username & Email Generator")

WINDOW_WIDTH = 420
WINDOW_HEIGHT = 480

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = screen_width - WINDOW_WIDTH
y = screen_height - WINDOW_HEIGHT

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

tk.Button(root, text="Sign Up", command=on_submit).pack(pady=10)

#
first_name_entry.insert(0, DEFAULT_FIRST_NAME)
last_name_entry.insert(0, DEFAULT_LAST_NAME)
password_entry.insert(0, DEFAULT_PASSWORD)


if __name__ == "__main__":
    root.mainloop()