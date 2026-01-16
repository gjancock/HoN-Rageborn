import requests
import subprocess
import sys
import os
from packaging import version
import configparser
import tkinter as tk
from tkinter import ttk
import ctypes
import hashlib
from utilities.constants import DEFAULT_ACCOUNT_EMAIL_DOMAIN, DEFAULT_ACCOUNT_FIRSTNAME, DEFAULT_ACCOUNT_LASTNAME, DEFAULT_ACCOUNT_PASSWORD

# --------------------------------------------------
# Identity (taskbar / icon grouping)
# --------------------------------------------------
def set_app_id():
    app_id = "gjancock.Rageborn"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

set_app_id()

# --------------------------------------------------
# Paths (ALWAYS relative to launcher.exe)
# --------------------------------------------------
def exe_dir():
    return os.path.dirname(os.path.abspath(sys.executable))

BASE_DIR = exe_dir()

APP_EXE = os.path.join(BASE_DIR, "Rageborn.exe")          # MAIN APP
TEMP_EXE = os.path.join(BASE_DIR, "Rageborn.new.exe")
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

# --------------------------------------------------
# Config
# --------------------------------------------------
CONFIG_SETTINGS_SECTION = "settings"
CONFIG_ACCOUNT_SECTION = "account"
CONFIG_AUTO_UPDATE_KEY = "auto_update"
CONFIG_FIRSTNAME_KEY = "firstname"
CONFIG_LASTNAME_KEY = "lastname"
CONFIG_EMAIL_DOMAIN_KEY = "email_domain"
CONFIG_PASSWORD_KEY = "password"

REPO = "gjancock/HoN-Rageborn"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def app_exists():
    return os.path.exists(APP_EXE)

def auto_update_enabled():
    config = configparser.ConfigParser()
    try:
        config.read(CONFIG_FILE, encoding="utf-8")
        if config.has_section(CONFIG_SETTINGS_SECTION) and config.has_option(CONFIG_SETTINGS_SECTION, CONFIG_AUTO_UPDATE_KEY):
            return config.getboolean(CONFIG_SETTINGS_SECTION, CONFIG_AUTO_UPDATE_KEY)
    except Exception:
        pass
    return True  # default ON

def read_local_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"

def get_latest_release():
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    remote_version = data["tag_name"].lstrip("v")
    exe_url = None
    sha_url = None

    for asset in data["assets"]:
        if asset["name"] == "Rageborn.exe":
            exe_url = asset["browser_download_url"]
        elif asset["name"] == "Rageborn.exe.sha256":
            sha_url = asset["browser_download_url"]

    if not exe_url:
        raise RuntimeError(
            "Rageborn.exe not found in release assets.\n"
            "This usually means the release was published incorrectly.\n"
            "Please report this issue to gjancock."
        )

    if not sha_url:
        raise RuntimeError(
            "Rageborn.exe.sha256 not found in release assets.\n"
            "Checksum verification is required.\n"
            "Please report this issue to gjancock."
        )

    return remote_version, exe_url, sha_url


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()



def ensure_config_exists():
    if os.path.exists(CONFIG_FILE):
        return

    config = configparser.ConfigParser()
    config[CONFIG_SETTINGS_SECTION] = {
        CONFIG_AUTO_UPDATE_KEY: "true"
    }
    config[CONFIG_ACCOUNT_SECTION] = {
        CONFIG_FIRSTNAME_KEY: DEFAULT_ACCOUNT_FIRSTNAME,
        CONFIG_LASTNAME_KEY: DEFAULT_ACCOUNT_LASTNAME,
        CONFIG_PASSWORD_KEY: DEFAULT_ACCOUNT_PASSWORD,
        CONFIG_EMAIL_DOMAIN_KEY: DEFAULT_ACCOUNT_EMAIL_DOMAIN
    }

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
    except Exception:
        pass  # launcher must not crash because of config


def get_remote_hash(sha_url):
    r = requests.get(sha_url, timeout=10)
    r.raise_for_status()
    return r.text.split()[0]


def needs_download(app_path, remote_hash):
    if not os.path.exists(app_path):
        return True

    try:
        local_hash = sha256_of_file(app_path)
        return local_hash != remote_hash
    except Exception:
        return True


# --------------------------------------------------
# UI
# --------------------------------------------------
class UpdateUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rageborn Updater")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        # --- TEXT BOX (instead of Label) ---
        self.text = tk.Text(
            self.root,
            width=45,
            height=8,   # ⬅ taller baseline
            wrap="word",
            borderwidth=0,
            highlightthickness=0
        )

        self.text.pack(padx=20, pady=(20, 10))
        self.text.config(state="disabled")

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=15, pady=5)

        self.progress = ttk.Progressbar(
            self.root, length=320, mode="determinate"
        )
        self.progress.pack(padx=20, pady=(0, 15))

        self.center()
        self.root.update()

    def center(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def set_text(self, text):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.config(state="disabled")

        # Auto-resize height based on content
        lines = int(self.text.index("end-1c").split(".")[0])
        self.text.config(height=min(max(lines, 6), 12))
        
        self.center()
        self.root.update()

    def set_progress(self, value):
        self.progress["value"] = value
        self.root.update()

    def close(self):
        self.root.destroy()


# --------------------------------------------------
# Download
# --------------------------------------------------
def download(url, dest, ui):
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0

        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    ui.set_progress(downloaded * 100 / total)

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    ensure_config_exists() 

    ui = UpdateUI()
    local_version = read_local_version()

    try:
        # FIRST RUN (bootstrap)
        if not app_exists():
            ui.set_text("Installing Rageborn...")
            remote, exe_url, sha_url = get_latest_release()
            remote_hash = get_remote_hash(sha_url)

            ui.set_text("Installing Rageborn...")
            download(exe_url, TEMP_EXE, ui)
            os.replace(TEMP_EXE, APP_EXE)

            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(remote)

        # NORMAL UPDATE FLOW
        elif auto_update_enabled():
            ui.set_text("Checking for updates...")
            remote, exe_url, sha_url = get_latest_release()
            remote_hash = get_remote_hash(sha_url)

            if needs_download(APP_EXE, remote_hash):
                ui.set_text(f"Updating to v{remote}...")
                download(exe_url, TEMP_EXE, ui)
                os.replace(TEMP_EXE, APP_EXE)

                with open(VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(remote)
            else:
                ui.set_text("Rageborn is up to date.")

        else:
            ui.set_text("Auto-update disabled.")

    except Exception as e:
        # 🔴 HARD STOP WITH MESSAGE
        ui.set_text(f"Update failed:\n{e}")
        ui.root.mainloop()
        return

    # SUCCESS PATH
    ui.set_text("Starting Rageborn...")
    ui.root.after(600, ui.close)

    try:
        subprocess.Popen([APP_EXE], close_fds=True)
    except Exception as e:
        ui.set_text(f"Failed to start app:\n{e}")
        ui.root.mainloop()
        return

    sys.exit(0)

# --------------------------------------------------
if __name__ == "__main__":
    main()
