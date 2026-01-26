# ui/game_launcher.py
import os
import subprocess
import logging
from tkinter import filedialog, messagebox
import core.state as state
from utilities.gameConfigUtilities import prepare_game_config

logger = logging.getLogger("rageborn")


def browse_executable(game_exe_var, exe_entry):
    exe_path = filedialog.askopenfilename(
        title="Select Juvio Game Executable",
        filetypes=[("Executable files", "*.exe")]
    )

    if not exe_path:
        return

    if os.path.basename(exe_path).lower() != "juvio.exe":
        messagebox.showerror(
            "Invalid Game Launcher",
            "Invalid executable selected.\n\nPlease select:\njuvio.exe"
        )
        return

    if not os.path.isfile(exe_path):
        messagebox.showerror("Error", "Selected file does not exist")
        return

    game_exe_var.set(exe_path)
    state.set_game_executable(exe_path)
    logger.info(f"[INFO] Game executable set: {exe_path}")

    exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))


def validate_game_executable(game_exe_var, show_error=True):
    exe = game_exe_var.get()

    if not exe:
        if show_error:
            messagebox.showerror("Error", "Please select game launcher first.")
        return False

    if not os.path.isfile(exe):
        if show_error:
            messagebox.showerror(
                "Executable missing",
                "The selected executable no longer exists."
            )
        return False

    if os.path.basename(exe).lower() != "juvio.exe":
        if show_error:
            messagebox.showerror(
                "Invalid Game Launcher",
                "Configured executable is not juvio.exe."
            )
        return False

    return True


def launch_game_process(game_exe_var):
    exe = game_exe_var.get()

    if not validate_game_executable(game_exe_var):
        return False

    prepare_game_config(
        logger=logger,
        window_mode=2,
        width=1024,
        height=768
    )

    subprocess.Popen([exe], cwd=os.path.dirname(exe))
    return True


def on_browse_executable(
    *,
    game_exe_var,
    exe_entry,
):
    from tkinter import filedialog, messagebox
    import os
    import core.state as state

    exe_path = filedialog.askopenfilename(
        title="Select Juvio Game Executable",
        filetypes=[("Executable files", "*.exe")]
    )

    if not exe_path:
        return

    if os.path.basename(exe_path).lower() != "juvio.exe":
        messagebox.showerror(
            "Invalid Game Launcher",
            "Invalid executable selected.\n\nPlease select:\njuvio.exe"
        )
        return

    if not os.path.isfile(exe_path):
        messagebox.showerror("Error", "Selected file does not exist")
        return

    game_exe_var.set(exe_path)
    state.set_game_executable(exe_path)

    logger.info(f"[INFO] Game executable set: {exe_path}")
    exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))


def cancel_auto_start_endless(
    *,
    root,
    countdown_var,
    autostart_module,
):
    autostart_module.cancel_auto_start(root, countdown_var)
    logger.info("[INFO] Auto-start Endless Mode cancelled")
