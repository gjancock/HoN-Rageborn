import subprocess
import hashlib
import sys
from pathlib import Path

# -----------------------------
# Config
# -----------------------------
APP_NAME = "Rageborn"
EXE_NAME = "Rageborn.exe"
DIST_DIR = Path("dist")

# -----------------------------
# Helpers
# -----------------------------
def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# -----------------------------
# Build
# -----------------------------
def build_exe():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
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

        # Data files
        "--add-data", "VERSION;.",
        "--add-data", "images;images",
        "--add-data", "datasets;datasets",
        "--add-data", "scripts;scripts",
        "--add-data", "data;data",

        "ragebirth.py"
    ]

    subprocess.check_call(cmd)


# -----------------------------
# Write checksum
# -----------------------------
def write_sha256():
    exe_path = DIST_DIR / EXE_NAME

    if not exe_path.exists():
        raise RuntimeError("Build failed: Rageborn.exe not found")

    sha = sha256_of_file(exe_path)
    sha_file = exe_path.with_suffix(".exe.sha256")

    sha_file.write_text(
        f"{sha}  {exe_path.name}\n",
        encoding="utf-8"
    )

    print(f"[OK] Generated {sha_file.name}")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    build_exe()
    write_sha256()
