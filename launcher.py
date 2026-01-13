import requests
import subprocess
import sys
import os
from packaging import version
import configparser
import tkinter as tk
from tkinter import ttk
import ctypes

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
CONFIG_SECTION = "settings"
CONFIG_KEY = "auto_update"

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
        if config.has_section(CONFIG_SECTION) and config.has_option(CONFIG_SECTION, CONFIG_KEY):
            return config.getboolean(CONFIG_SECTION, CONFIG_KEY)
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
    download_url = None

    for asset in data["assets"]:
        if asset["name"] == "Rageborn.exe":
            download_url = asset["browser_download_url"]

    if not download_url:
        raise RuntimeError(
            "Rageborn.exe not found in release assets.\n"
            "This usually means the release was published incorrectly.\n"
            "Please report this issue to gjancock."
        )

    return remote_version, download_url

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
    ui = UpdateUI()
    local_version = read_local_version()

    try:
        # FIRST RUN (bootstrap)
        if not app_exists():
            ui.set_text("Installing Rageborn...")
            remote, url = get_latest_release()
            download(url, TEMP_EXE, ui)
            os.replace(TEMP_EXE, APP_EXE)

            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(remote)

        # NORMAL UPDATE FLOW
        elif auto_update_enabled():
            ui.set_text("Checking for updates...")
            remote, url = get_latest_release()

            if version.parse(remote) > version.parse(local_version):
                ui.set_text(f"Updating to v{remote}...")
                download(url, TEMP_EXE, ui)
                os.replace(TEMP_EXE, APP_EXE)

                with open(VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(remote)
            else:
                ui.set_text("No updates found.")

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
