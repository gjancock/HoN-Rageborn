import subprocess
import hashlib
import sys
import shutil
from pathlib import Path

# -----------------------------
# Config
# -----------------------------
APP_NAME = "Rageborn"
EXE_NAME = "Rageborn.exe"

DIST_DIR = Path("dist")
BUILD_DIR = DIST_DIR / APP_NAME        # dist/Rageborn/
ZIP_NAME = f"{APP_NAME}-win64.zip"     # Rageborn-win64.zip
ZIP_PATH = DIST_DIR / ZIP_NAME

# -----------------------------
# Helpers
# -----------------------------
def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_zip_sha256(zip_path: Path):
    sha = sha256_of_file(zip_path)
    sha_file = zip_path.with_suffix(".zip.sha256")

    sha_file.write_text(
        f"{sha}  {zip_path.name}\n",
        encoding="utf-8"
    )

    print(f"[OK] Generated {sha_file.name}")
    return sha


# -----------------------------
# Build EXE (UNCHANGED LOGIC)
# -----------------------------
def build_exe():
    cmd = [
        sys.executable, "-m", "PyInstaller",

        # IMPORTANT: onedir (NOT onefile)
        "--onedir",
        "--noconsole",
        "--name", APP_NAME,

        # Core runtime
        "--hidden-import=pyautogui",
        "--hidden-import=pyscreeze",
        "--hidden-import=pygetwindow",
        "--hidden-import=pymsgbox",
        "--hidden-import=mouseinfo",
        "--hidden-import=cv2",
        "--hidden-import=win32gui",
        "--hidden-import=win32con",
        "--hidden-import=win32process",
        "--hidden-import=keyboard",

        # Internal modules (defensive)
        "--hidden-import=core.state",
        "--hidden-import=ui.autostart",
        "--hidden-import=ui.game_launcher",
        "--hidden-import=ui.chat_editor",
        "--hidden-import=ui.cycle_runner",
        "--hidden-import=ui.ui_handlers",
        "--hidden-import=ui.ui_state_sync",
        "--hidden-import=ui.rageborn_runner",
        "--hidden-import=ui.log_view",

        # UI safety
        "--hidden-import=tkinter",

        # Data files (UNCHANGED)
        "--add-data", "VERSION;.",
        "--add-data", "images;images",
        "--add-data", "datasets;datasets",
        "--add-data", "scripts;scripts",
        "--add-data", "data;data",
        "--add-data", "assets;assets",

        "ragebirth.py"
    ]

    subprocess.check_call(cmd)


# -----------------------------
# Package ZIP
# -----------------------------
def create_release_zip():
    """
    Zip dist/Rageborn/ into Rageborn-win64.zip
    """

    if not BUILD_DIR.exists():
        raise RuntimeError(f"Build directory not found: {BUILD_DIR}")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print(f"[INFO] Creating release zip: {ZIP_NAME}")

    shutil.make_archive(
        base_name=str(ZIP_PATH.with_suffix("")),
        format="zip",
        root_dir=DIST_DIR,
        base_dir=APP_NAME,
    )

    print(f"[OK] Created {ZIP_PATH}")


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    build_exe()
    create_release_zip()
    sha = write_zip_sha256(ZIP_PATH)

    print("\n=== RELEASE READY ===")
    print(f"ZIP     : {ZIP_PATH.name}")
    print(f"SHA256  : {sha}")
    print("\nUpload BOTH files to GitHub Release:")
    print(f"- {ZIP_PATH.name}")
    print(f"- {ZIP_PATH.with_suffix('.zip.sha256').name}")
