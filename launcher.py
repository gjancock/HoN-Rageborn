import requests
import subprocess
import sys
import os
import time
import configparser
import tkinter as tk
import ctypes
import hashlib
import zipfile
import shutil
import traceback # Debug

from tkinter import ttk
from utilities.constants import DEFAULT_ACCOUNT_EMAIL_DOMAIN, DEFAULT_ACCOUNT_FIRSTNAME, DEFAULT_ACCOUNT_LASTNAME, DEFAULT_ACCOUNT_PASSWORD
from utilities.paths import (
    CONFIG_PATH,
    VERSION_FILE,
    RAGEBORN_EXE,
    TESSERACT_EXE,
    TESSERACT_DIR,
    TESSERACT_RUNTIME_DIR,
    get_launcher_dir,
    RAGEBORN_DIR,
)

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
BASE_DIR = get_launcher_dir()

APP_DIR = RAGEBORN_DIR
APP_EXE = str(RAGEBORN_EXE)

CONFIG_FILE = str(CONFIG_PATH)

RAGEBORN_ZIP = get_launcher_dir() / "Rageborn-win64.zip"
RAGEBORN_SHA_LOCAL = RAGEBORN_DIR / "installed.sha256"

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

TESSERACT_ZIP_URL = (
    "https://github.com/gjancock/HoN-Rageborn/releases/"
    "download/ocr-v1.0.0/tesseract-5.3.3-win64.zip"
)
TESSERACT_SHA_URL = (
    "https://github.com/gjancock/HoN-Rageborn/releases/"
    "download/ocr-v1.0.0/tesseract-5.3.3-win64.zip.sha256"
)
TESSERACT_SHA_LOCAL = os.path.join(TESSERACT_DIR, "installed.sha256")


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
    zip_url = None
    sha_url = None

    for asset in data["assets"]:
        if asset["name"] == "Rageborn-win64.zip":
            zip_url = asset["browser_download_url"]
        elif asset["name"] == "Rageborn-win64.zip.sha256":
            sha_url = asset["browser_download_url"]

    if not zip_url or not sha_url:
        raise RuntimeError(
            "Rageborn release assets incomplete.\n"
            "Expected Rageborn-win64.zip and Rageborn-win64.zip.sha256"
        )

    return remote_version, zip_url, sha_url


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
   

def is_network_error(e: Exception) -> bool:
    return isinstance(e, (
        IOError,
        OSError,
        requests.exceptions.RequestException,
        zipfile.BadZipFile,
    ))


def retry_countdown(ui, seconds):
    for i in range(seconds, 0, -1):
        ui.set_text(
            "Update failed due to connection issue.\n\n"
            f"Retrying in {i} seconds..."
        )
        time.sleep(1)


def download_text(url: str) -> str:
    """
    Download a small text file (e.g. .sha256) and return its content.
    """
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text.strip()


def ensure_tesseract(ui=None):
    from utilities.paths import (
        TESSERACT_DIR,
        TESSERACT_EXE,
        TESSERACT_RUNTIME_DIR,
        get_user_data_dir,
    )

    expected_sha = download_text(TESSERACT_SHA_URL).split()[0]
    sha_record = TESSERACT_DIR / "installed.sha256"

    # Already installed & valid
    if TESSERACT_EXE.exists() and sha_record.exists():
        if sha_record.read_text().strip() == expected_sha:
            return

    if ui:
        ui.set_text("Installing OCR engine...")

    # ✅ Download ZIP to a SAFE temp location
    temp_zip = get_user_data_dir() / "tesseract.zip"

    # Clean any previous temp zip
    temp_zip.unlink(missing_ok=True)

    download(TESSERACT_ZIP_URL, temp_zip, ui)

    # Verify ZIP
    actual_sha = sha256_of_file(temp_zip)
    if actual_sha != expected_sha:
        temp_zip.unlink(missing_ok=True)
        raise IOError("Tesseract checksum mismatch")

    # ❗ NOW it is safe to delete runtime
    shutil.rmtree(TESSERACT_RUNTIME_DIR, ignore_errors=True)

    # Extract ZIP ROOT to USER DATA DIR
    with zipfile.ZipFile(temp_zip, "r") as z:
        z.extractall(get_user_data_dir())

    temp_zip.unlink(missing_ok=True)

    # Hard verify install
    if not TESSERACT_EXE.exists():
        raise OSError(
            f"Tesseract install incomplete.\n"
            f"Expected: {TESSERACT_EXE}"
        )

    # Mark installed ONLY after success
    sha_record.write_text(expected_sha)


def ensure_rageborn(ui=None):
    os.makedirs(BASE_DIR, exist_ok=True)

    remote_version, zip_url, sha_url = get_latest_release()
    expected_sha = download_text(sha_url).split()[0]

    # Already installed & matches
    if os.path.exists(APP_EXE) and os.path.exists(RAGEBORN_SHA_LOCAL):
        installed_sha = open(RAGEBORN_SHA_LOCAL, "r").read().strip()
        if installed_sha == expected_sha:
            return

    if ui:
        ui.set_text("Installing / Updating Rageborn...")

    ui.set_progress(0)

    # Download ZIP
    download(zip_url, RAGEBORN_ZIP, ui)

    # Verify ZIP
    actual_sha = sha256_of_file(RAGEBORN_ZIP)
    if actual_sha != expected_sha:
        os.remove(RAGEBORN_ZIP)
        raise RuntimeError("Rageborn checksum mismatch")

    # Clean old install
    shutil.rmtree(APP_DIR, ignore_errors=True)
    os.makedirs(APP_DIR, exist_ok=True)

    # Extract ZIP (contains Rageborn/ folder)
    with zipfile.ZipFile(RAGEBORN_ZIP, "r") as z:
        z.extractall(BASE_DIR)

    os.remove(RAGEBORN_ZIP)

    # Record installed SHA + version
    with open(RAGEBORN_SHA_LOCAL, "w", encoding="utf-8") as f:
        f.write(expected_sha)

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(remote_version)

    if not os.path.exists(APP_EXE):
        raise RuntimeError("Rageborn install incomplete")


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

    MAX_RETRIES = 5
    RETRY_DELAY = 10  # seconds

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ui.set_text(f"Preparing Rageborn... (Attempt {attempt}/{MAX_RETRIES})")

            if auto_update_enabled():
                ensure_rageborn(ui)
            else:
                if not os.path.exists(APP_EXE):
                    raise RuntimeError("Rageborn not installed")

            ui.set_text("Installing OCR engine...")
            ensure_tesseract(ui)

            break  # ✅ success

        except Exception as e:
            if is_network_error(e) and attempt < MAX_RETRIES:
                ui.set_text(
                    f"Temporary error occurred.\n"
                    f"Retrying in {RETRY_DELAY} seconds...\n\n"
                    f"{e}"
                )
                retry_countdown(ui, RETRY_DELAY)
                continue

            ui.set_text(
                "Update failed permanently:\n\n"
                f"{e}\n\n"
                "Please check your internet connection."
            )
            # Debug
            # ui.set_text(
            #     "Update failed permanently:\n\n"
            #     f"{repr(e)}\n\n"
            #     f"{traceback.format_exc()}"
            # )
            ui.root.mainloop()
            return


    # -------------------------------
    # SUCCESS PATH
    # -------------------------------
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
