import os
import sys
from pathlib import Path


# ============================================================
# Base helpers
# ============================================================

def is_frozen() -> bool:
    """
    Returns True if running from a PyInstaller bundle.
    """
    return getattr(sys, "frozen", False)


from pathlib import Path
import sys

def get_launcher_dir() -> Path:
    """
    Directory containing bundled runtime assets.

    Frozen:
        dist/Rageborn/_internal
    Dev:
        project root
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        internal = exe_dir / "_internal"
        return internal if internal.exists() else exe_dir

    # dev mode
    return Path(__file__).resolve().parents[1]


def get_app_runtime_dir() -> Path:
    """
    Directory where Rageborn.exe resides.
    For onedir layout:
        launcher.exe
        Rageborn/
            Rageborn.exe  <-- this path
    """
    if is_frozen():
        return Path(sys.executable).parent
    return Path.cwd()


def get_user_data_dir() -> Path:
    """
    Persistent user data directory.
    This directory MUST survive updates.
    """
    base = os.environ.get("APPDATA")
    if not base:
        raise RuntimeError("APPDATA environment variable not found")

    path = Path(base) / "Rageborn"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ============================================================
# Canonical application paths (USE THESE)
# ============================================================

# ---- Config ----
CONFIG_PATH = get_user_data_dir() / "config.ini"

# ---- Logs ----
LOG_DIR = get_user_data_dir() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ---- Version ----
VERSION_FILE = get_user_data_dir() / "VERSION"

# ---- Signup / accounts ----
SIGNUP_USERS_FILE = get_user_data_dir() / "signup_users.txt"

# ---- Runtime OCR ----
TESSERACT_RUNTIME_DIR = get_user_data_dir() / "tesseract_runtime"
TESSERACT_DIR = TESSERACT_RUNTIME_DIR / "tesseract"
TESSERACT_EXE = TESSERACT_DIR / "tesseract.exe"
TESSDATA_DIR = TESSERACT_DIR / "tessdata"

# ---- Rageborn runtime ----
RAGEBORN_DIR = get_launcher_dir() / "Rageborn"
RAGEBORN_EXE = RAGEBORN_DIR / "Rageborn.exe"
