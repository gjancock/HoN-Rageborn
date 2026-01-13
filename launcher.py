import requests
import subprocess
import sys
import os
from packaging import version
import configparser
import tkinter as tk
from tkinter import ttk
import ctypes

CONFIG_FILE = "config.ini"
CONFIG_SECTION = "settings"
CONFIG_KEY = "auto_update"

REPO = "gjancock/HoN-Rageborn"
APP_EXE = "RagebornApp.exe"
TEMP_EXE = "Rageborn.new.exe"
VERSION_FILE = "VERSION"

API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"


def set_app_id():
    app_id = "gjancock.Rageborn"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

set_app_id()

def auto_update_enabled():
    config = configparser.ConfigParser()

    try:
        config.read(CONFIG_FILE, encoding="utf-8")

        if config.has_section(CONFIG_SECTION) and config.has_option(CONFIG_SECTION, CONFIG_KEY):
            return config.getboolean(CONFIG_SECTION, CONFIG_KEY)

    except Exception:
        pass

    # Safe default: auto-update ON
    return True


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
        if asset["name"] == APP_EXE:
            download_url = asset["browser_download_url"]

    if not download_url:
        raise RuntimeError(f"{APP_EXE} not found in release assets")

    return remote_version, download_url


class UpdateUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rageborn Updater")
        self.root.resizable(False, False)

        self.label = ttk.Label(self.root, text="Checking for updates...")
        self.label.pack(padx=20, pady=(15, 5))

        self.progress = ttk.Progressbar(
            self.root, length=260, mode="determinate"
        )
        self.progress.pack(padx=20, pady=(0, 15))

        # 🔽 IMPORTANT: force size calculation
        self.root.update_idletasks()

        # 🔽 Center the window
        self.center_window()

        self.root.update()

    def center_window(self):
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def set_text(self, text):
        self.label.config(text=text)
        self.root.update()

    def set_progress(self, value):
        self.progress["value"] = value
        self.root.update()

    def close(self):
        self.root.destroy()


def download(url, dest, ui: UpdateUI):
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
                    percent = downloaded * 100 / total
                    ui.set_progress(percent)


def main():
    ui = UpdateUI()
    local = read_local_version()

    try:
        if auto_update_enabled():
            ui.set_text("Checking for updates...")
            remote, url = get_latest_release()

            if version.parse(remote) > version.parse(local):
                ui.set_text(f"Downloading update v{remote}...")
                download(url, TEMP_EXE, ui)

                ui.set_text("Applying update...")
                os.replace(TEMP_EXE, APP_EXE)

                with open(VERSION_FILE, "w", encoding="utf-8") as f:
                    f.write(remote)
            else:
                ui.set_text("No updates found.")
        else:
            ui.set_text("Auto-update disabled.")

    except Exception as e:
        ui.set_text("Update skipped.")

    ui.set_text("Starting Rageborn...")
    ui.close()

    subprocess.Popen([APP_EXE], close_fds=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
