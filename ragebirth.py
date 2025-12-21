import tkinter as tk
from tkinter import messagebox
import requests
import re
from urllib.parse import urlencode

BASE_URL = "https://app.juvio.com"
SIGNUP_URL = BASE_URL + "/signup"

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
        return True, "Signup successful!"
    else:
        return False, r.text


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
        messagebox.showinfo("Success", msg)
    else:
        messagebox.showerror("Failed", msg)


root = tk.Tk()
root.title("Signup Tool")
root.geometry("350x300")

tk.Label(root, text="First Name").pack()
first_name_entry = tk.Entry(root)
first_name_entry.pack()

tk.Label(root, text="Last Name").pack()
last_name_entry = tk.Entry(root)
last_name_entry.pack()

tk.Label(root, text="Email").pack()
email_entry = tk.Entry(root)
email_entry.pack()

tk.Label(root, text="Username").pack()
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Password").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

tk.Button(root, text="Sign Up", command=on_submit).pack(pady=10)

root.mainloop()
