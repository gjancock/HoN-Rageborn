import logging
import tkinter as tk
import random
import subprocess
import threading
import time
import utilities.constants as constant
import os
import core.state as state
import configparser
import pyautogui
import time
import subprocess
import psutil

from datetime import datetime
from tkinter import messagebox
from queue import Queue
from utilities.loggerSetup import setup_logger
# Logger
log_queue = Queue()
logger = setup_logger(ui_queue=log_queue)
ui_formatter = logging.Formatter(
    "%(asctime)s | %(message)s",
    "%H:%M:%S"
)
from utilities.config import load_config
# Load Config at startup
config = load_config()
from utilities.usernameGenerator import (
    generate_counter_username, 
    generate_word_username, 
    reset_prefix_counters, 
    reset_postfix_counters, 
    set_prefix_counters, 
    set_postfix_counters
)
from utilities.ipAddressGenerator import random_public_ip
from tkinter import filedialog
from tkinter import ttk
from utilities.gameConfigUtilities import prepare_game_config
from utilities.chatUtilities import (
    get_chat_path,
    read_chat_file,
    validate_chat_lines,
    save_chat_file
)
from utilities.runtime import runtime_dir
from utilities.emailGenerator import generate_email
from utilities.accountRegistration import signup_user

#
auto_start_time = None
iteration_count = 0

#
auto_start_timer_id = None
AUTO_START_DELAY_MS = 5000  # 5 seconds
auto_start_countdown_id = None
AUTO_START_DELAY_SECONDS = 5
auto_start_remaining = 0

# CHAT DATA
MAX_CHAT_LEN = 150

# ============================================================
# APPLICATION SETTINGS
# ============================================================
def set_self_high_priority():
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        logger.info("[PRIORITY] Python process set to HIGH")

    except psutil.AccessDenied:
        logger.warning("[PRIORITY] Access denied – priority unchanged")

    except Exception as e:
        logger.warning(f"[PRIORITY] Failed to set priority: {e}")


def global_thread_exception_handler(args):
    logger.exception(
        "[THREAD-CRASH] Unhandled exception",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )

threading.excepthook = global_thread_exception_handler

def read_version():
    try:
        path = os.path.join(runtime_dir(), "VERSION")
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        logger.error("[ERROR] Unable to find VERSION")
        return "unknown"
    
#
INFO_NAME = "Rageborn"
VERSION = read_version()

# ============================================================
# UI CALLBACKS
# ============================================================

def schedule_auto_start_endless():
    global auto_start_timer_id

    # Avoid double scheduling
    if auto_start_timer_id is not None:
        return

    logger.info("[INFO] Auto-start Endless Mode scheduled in 5 seconds")

    auto_start_timer_id = root.after(
        AUTO_START_DELAY_MS,
        execute_auto_start_endless
    )


def cancel_auto_start_endless():
    global auto_start_timer_id

    if auto_start_timer_id is not None:
        root.after_cancel(auto_start_timer_id)
        auto_start_timer_id = None
        logger.info("[INFO] Auto-start Endless Mode cancelled")


def execute_auto_start_endless():
    global auto_start_timer_id
    auto_start_timer_id = None

    # Final guard: user might untick at the last moment
    if auto_start_endless_var.get():
        logger.info("[INFO] Auto-starting Endless Mode now")
        on_start_endless_mode()
    else:
        logger.info("[INFO] Auto-start aborted (checkbox unchecked)")

def resetState():
    state.STOP_EVENT.clear()
    state.CRASH_EVENT.clear()

def run_rageborn_flow(username, password):
    try:
        if not launch_game_process():
            logger.error("[ERROR] Game launch aborted")
            return
        
        if state.SLOWER_PC_MODE:
            logger.info("[INFO] RAGEBORN slow mode activated.")

        import rageborn

        resetState()
        rageborn.start(username, password)

        if state.CRASH_EVENT.is_set():
            logger.exception("[FATAL] Rageborn crashed during runtime")
            raise

    except RuntimeError:
        raise
    except Exception:
        logger.exception("[FATAL] Rageborn crashed")
        raise
    except pyautogui.FailSafeException:
        logger.info("[SAFETY] FAILSAFE Triggered! Emergency stop.")
        state.STOP_EVENT.set()
        raise

    finally:
        kill_jokevio()
        logger.info("[MAIN] Rageborn thread exited")


def run_rageborn_flow_thread(username, password):
    try:
        run_rageborn_flow(username, password)
    except RuntimeError as e:
        logger.error(f"[THREAD-CRASH] {e}")
    except Exception:
        logger.exception("[THREAD-CRASH] Unexpected error")


def start_rageborn_async(username, password):    
    t = threading.Thread(
        target=run_rageborn_flow_thread,
        args=(username, password),
        daemon=True
    )
    t.start()

# ----------------- UI callbacks -----------------
def get_effective_password():
    pwd = password_entry.get().strip()
    return pwd if pwd else state.get_account_password()

def on_generate():
    prefix = prefix_entry.get().strip()
    postfix = postfix_entry.get().strip()
    domain = domain_entry.get().strip() or "mail.com"

    use_prefix_count = add_prefix_count_var.get()
    use_postfix_count = add_postfix_count_var.get()

    # 🔴 Counter-based generation
    if use_prefix_count or use_postfix_count:
        username, prefix_counter, postfix_counter = generate_counter_username(
            prefix=prefix,
            postfix=postfix,
            use_prefix_count=use_prefix_count,
            use_postfix_count=use_postfix_count,
            prefix_start=prefix_count_start_var.get(),
            postfix_start=postfix_count_start_var.get(),
        )

        if use_prefix_count:
            state.set_username_prefix_count_start_at(prefix_counter - 1)

        if use_postfix_count:
            state.set_username_postfix_count_start_at(postfix_counter - 1)

    else:
        # 🟢 Normal word-pool generator (existing behavior)
        username = generate_word_username(prefix, postfix)

    email = generate_email(prefix, postfix, domain)

    username_entry.delete(0, tk.END)
    username_entry.insert(0, username)

    email_entry.delete(0, tk.END)
    email_entry.insert(0, email)

def kill_jokevio():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "juvio.exe"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"[INFO] Jokevio.exe killed")
    except subprocess.CalledProcessError:
        logger.info(f"[INFO] Intend to kill Jokevio.exe, but its not running")

# ============================================================
# UI Application 
# ============================================================
root = tk.Tk()
root.update_idletasks()  # ensure geometry info is ready
root.title(f"{INFO_NAME} v{VERSION}")

auto_mode_var = tk.BooleanVar(value=False)
duration_var = tk.StringVar(value="Duration: 00:00:00")
iteration_var = tk.StringVar(value="Iterations completed: 0")
auto_start_endless_var = tk.BooleanVar(value=state.get_auto_start_endless())
auto_start_countdown_var = tk.StringVar(value="")
auto_email_verification_var = tk.BooleanVar(
    value=state.get_auto_email_verification()
)
auto_mobile_verification_var = tk.BooleanVar(
    value=state.get_auto_mobile_verification()
)
auto_update_var = tk.BooleanVar(value=state.get_auto_update())
auto_restart_dns_var = tk.BooleanVar(value=state.get_auto_restart_dns())
settings_for_slower_pc_var = tk.BooleanVar(value=state.get_settings_for_slower_pc())
is_ragequit_mode_enabled_var = tk.BooleanVar(value=state.get_is_ragequit_mode_enabled())

_last_prefix_enabled = state.get_username_prefix_count_enabled()
_last_postfix_enabled = state.get_username_postfix_count_enabled()

add_prefix_count_var = tk.BooleanVar(
    value=state.get_username_prefix_count_enabled()
)

add_postfix_count_var = tk.BooleanVar(
    value=state.get_username_postfix_count_enabled()
)

prefix_count_start_var = tk.IntVar(
    value=state.get_username_prefix_count_start_at()
)

postfix_count_start_var = tk.IntVar(
    value=state.get_username_postfix_count_start_at()
)

def make_debouncer(root, delay, func):
    job = None

    def wrapper(*args):
        nonlocal job
        if job:
            root.after_cancel(job)
        job = root.after(delay, lambda: func(*args))

    return wrapper


def one_full_cycle():
    try:
        while True:
            # 1️⃣ Generate username/email
            on_generate()

            # 2️⃣ Read generated credentials
            username = username_entry.get()
            password = get_effective_password()

            logger.info("-------------------------------------------")
            logger.info(f"[INFO] Generated account: {username}")

            # 3️⃣ Run signup
            try:
                success, msg = signup_user(
                    first_name_entry.get(),
                    last_name_entry.get(),
                    email_entry.get(),
                    username,
                    password
                )
            except Exception as e:
                logger.warning(f"[WARN] Signup exception, regenerating: {e}")
                success = False
                msg = "exception"
            
            if success:
                break
            
            logger.info(f"[INFO] Failed to signup account {username}: {msg}")
            logger.info("[INFO] Regenerating new account")
            time.sleep(random.uniform(1, 3))

        logger.info(f"[INFO] Signup success! ")
        logger.info(f"Username {username} launching Rageborn.exe")

        # 4️⃣ Run rageborn (blocking inside worker thread)
        run_rageborn_flow(username, password)

        return True
    except Exception:
        logger.exception("[WARN] Cycle error, recovering")
        time.sleep(10)
        raise

def auto_loop_worker():
    logger.info(f"[INFO] --Endless mode started--v{VERSION}")

    root.after(0, set_start_time)

    global iteration_count
    iteration_count = 0
    root.after(0, lambda: iteration_var.set("Iterations completed: 0"))

    while auto_mode_var.get():
        try:
            one_full_cycle()

            root.after(0, increment_iteration)

        except Exception as e:
            # ABSOLUTE LAST LINE OF DEFENSE
            logger.exception("[FATAL] Cycle crashed, recovering")

            # Cooldown to avoid rapid crash loops
            time.sleep(10)

            # Continue forever
            continue

    logger.info("[INFO] Endless mode stopped")

def set_start_time():
    global auto_start_time
    auto_start_time = datetime.now()
    duration_var.set("Duration: 00:00:00")
    
def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def increment_iteration():
    global iteration_count, auto_start_time

    iteration_count += 1
    iteration_var.set(f"Iterations completed: {iteration_count}")

    if auto_start_time:
        elapsed = int((datetime.now() - auto_start_time).total_seconds())
        duration_var.set(f"Duration: {format_duration(elapsed)}")


def validate_int_only(new_value: str) -> bool:
    if new_value == "":
        return True 
    return new_value.isdigit()


def poll_log_queue():
    while not log_queue.empty():
        record = log_queue.get()

        # 1️⃣ Convert LogRecord → string
        msg = ui_formatter.format(record)

        log_text.config(state="normal")

        # ---- LOG LEVEL DETECTION ----
        tag = "INFO"

        if (
            "[FATAL]" in msg
            or "Traceback" in msg
            or "RuntimeError" in msg
            or "Exception" in msg
            or record.levelname in ("ERROR", "CRITICAL")
        ):
            tag = "ERROR"
        elif record.levelname == "WARNING" or "[WARN]" in msg:
            tag = "WARN"

        # 2️⃣ Insert formatted string
        log_text.insert("end", msg + "\n", tag)
        log_text.see("end")
        log_text.config(state="disabled")

    root.after(100, poll_log_queue)


def on_login_only():
    user = username_entry.get().strip()
    pwd = get_effective_password()

    if not user or not pwd:
        messagebox.showerror("Error", "Username and password are required")
        return

    logger.info(f"[INFO] Logging in with existing account: {user}")
    start_rageborn_async(user, pwd)

def on_signup_only():
    """Sign up ONLY, no Rageborn"""
    on_submit()

def on_signup_and_run_once():
    """Sign up, then run Rageborn once"""
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = get_effective_password()

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_user(first, last, email, user, pwd)

    if success:
        start_rageborn_async(user, pwd)
    else:
        messagebox.showerror("Failed", msg)


def on_start_endless_mode():
    """Start endless mode (replaces checkbox)"""
    if not auto_mode_var.get():
        auto_mode_var.set(True)

        root.after(0, set_endless_mode_ui_running)

        threading.Thread(
            target=auto_loop_worker,
            daemon=True
        ).start()

def on_submit():
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = get_effective_password()

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_user(first, last, email, user, pwd)

    if success:
        logger.info("[INFO] Signup successful!")
    else:
        logger.error(f"[ERROR] Signup failed: {msg}")

def on_browse_executable():
    exe_path = filedialog.askopenfilename(
        title="Select Juvio Game Executable",
        filetypes=[("Executable files", "*.exe")]
    )

    if not exe_path:
        return  # user cancelled

    filename = os.path.basename(exe_path).lower()

    if filename != "juvio.exe":
        messagebox.showerror(
            "Invalid Game Launcher",
            "Invalid executable selected.\n\n"
            "Please select:\n"
            "juvio.exe"
        )
        return

    if not os.path.isfile(exe_path):
        messagebox.showerror("Error", "Selected file does not exist")
        return

    game_exe_var.set(exe_path)
    state.set_game_executable(exe_path)

    logger.info(f"[INFO] Game executable set: {exe_path}")
    exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))


def launch_game_process():
    exe = game_exe_var.get()

    if not exe:
        messagebox.showerror(
            "Error",
            "Please select game launcher first."
        )
        return False

    if not os.path.isfile(exe):
        messagebox.showerror(
            "Executable missing",
            "The selected executable no longer exists."
        )
        return False

    if os.path.basename(exe).lower() != "juvio.exe":
        messagebox.showerror(
            "Invalid Game Launcher",
            "Configured executable is not juvio.exe.\n"
            "Please re-select the correct file."
        )
        return False
    
    # Prepare startup.cfg
    prepare_game_config(
        logger=logger,
        window_mode=2,
        width=1024,
        height=768
    )

    subprocess.Popen(
        [exe],
        cwd=os.path.dirname(exe)
    )
    return True


def validate_game_executable(show_error=True):
    exe = game_exe_var.get()

    if not exe:
        if show_error:
            messagebox.showerror(
                "Error",
                "Please select game launcher first."
            )
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

def on_auto_start_checkbox_changed():    
    value = auto_start_endless_var.get()
    state.set_auto_start_endless(value)

    if value:
        # ✅ validate only (DO NOT LAUNCH)
        if not validate_game_executable():
            auto_start_endless_var.set(False)
            state.set_auto_start_endless(False)
            cancel_auto_start_endless()
            logger.error("[ERROR] Invalid game executable, auto-start cancelled")
            return

        # ✅ only schedule countdown
        schedule_auto_start_endless()

    else:
        cancel_auto_start_endless()


def try_auto_start_from_config():
    """
    Called on app startup when auto_start=true in config.
    Must validate executable before scheduling countdown.
    """
    if not auto_start_endless_var.get():
        return

    if not validate_game_executable(show_error=False):
        logger.error(
            "[ERROR] Auto-start enabled in config, but game executable is invalid. Auto-start disabled."
        )

        auto_start_endless_var.set(False)
        state.set_auto_start_endless(False)
        auto_start_countdown_var.set("")
        return

    schedule_auto_start_endless()


def update_auto_start_countdown():
    global auto_start_remaining, auto_start_countdown_id

    if auto_start_remaining <= 0:
        auto_start_countdown_var.set("")
        auto_start_countdown_id = None
        execute_auto_start_endless()
        return

    auto_start_countdown_var.set(
        f"Auto start in {auto_start_remaining}…"
    )
    auto_start_remaining -= 1

    auto_start_countdown_id = root.after(1000, update_auto_start_countdown)


def schedule_auto_start_endless():    
    global auto_start_timer_id, auto_start_remaining

    if auto_start_timer_id is not None:
        return  # already scheduled

    auto_start_remaining = AUTO_START_DELAY_SECONDS
    auto_start_countdown_var.set(
        f"Auto start in {auto_start_remaining}…"
    )

    logger.info("[INFO] Auto-start Endless Mode scheduled")

    auto_start_timer_id = True  # logical flag
    update_auto_start_countdown()


def cancel_auto_start_endless():
    global auto_start_timer_id, auto_start_countdown_id

    if auto_start_countdown_id is not None:
        root.after_cancel(auto_start_countdown_id)
        auto_start_countdown_id = None

    auto_start_timer_id = None
    auto_start_countdown_var.set("")

    logger.info("[INFO] Auto-start Endless Mode cancelled")


def execute_auto_start_endless():
    global auto_start_timer_id

    auto_start_timer_id = None

    if auto_start_endless_var.get():
        logger.info("[INFO] Auto-starting Endless Mode now")
        root.after(0, set_endless_mode_ui_running)
        on_start_endless_mode()
    else:
        logger.info("[INFO] Auto-start aborted (checkbox unchecked)")


def labeled_entry(parent, label, default=""):
    tk.Label(parent, text=label, anchor="w").pack(fill="x")
    e = tk.Entry(parent)
    e.pack(fill="x", pady=2)
    if default:
        e.insert(0, default)
    return e

def set_endless_mode_ui_running():
    start_endless_btn.config(
        text="Hit F11 to stop",
        fg="red",
        state="disabled"
    )

def set_endless_mode_ui_idle():
    start_endless_btn.config(
        text="Start Endless Mode",
        fg="black",
        state="normal"
    )

def on_auto_email_verification_changed():
    state.set_auto_email_verification(
        auto_email_verification_var.get()
    )

def on_auto_mobile_verification_changed():
    state.set_auto_mobile_verification(
        auto_mobile_verification_var.get()
    )

def on_auto_update_changed():
    state.set_auto_update(
        auto_update_var.get()
    )

def on_username_prefix_add_count_changed():
    state.set_username_prefix_count_enabled(add_prefix_count_var.get())

def on_username_postfix_add_count_changed():
    state.set_username_postfix_count_enabled(add_postfix_count_var.get())

def on_prefix_checkbox_toggle():
    global _last_prefix_enabled

    enabled = add_prefix_count_var.get()

    if enabled and not _last_prefix_enabled:
        prefix_count_start_var.set(1)
        state.set_username_prefix_count_start_at(1)
        reset_prefix_counters()

    prefix_count_entry.config(
        state="normal" if enabled else "disabled"
    )

    state.set_username_prefix_count_enabled(enabled)
    _last_prefix_enabled = enabled


def on_postfix_checkbox_toggle():
    global _last_postfix_enabled

    enabled = add_postfix_count_var.get()

    if enabled and not _last_postfix_enabled:
        postfix_count_start_var.set(1)
        state.set_username_postfix_count_start_at(1)
        reset_postfix_counters()

    postfix_count_entry.config(
        state="normal" if enabled else "disabled"
    )

    state.set_username_postfix_count_enabled(enabled)
    _last_postfix_enabled = enabled

def on_prefix_count_changed(*_):
    if not add_prefix_count_var.get():
        return

    try:
        value = prefix_count_start_var.get()
    except tk.TclError:
        return  # user is still typing / entry temporarily empty

    state.set_username_prefix_count_start_at(value)
    set_prefix_counters(value)


def on_postfix_count_changed(*_):
    if not add_postfix_count_var.get():
        return

    try:
        value = postfix_count_start_var.get()
    except tk.TclError:
        return

    state.set_username_postfix_count_start_at(value)
    set_postfix_counters(value)


prefix_count_start_var.trace_add("write", on_prefix_count_changed)
postfix_count_start_var.trace_add("write", on_postfix_count_changed)


def force_newline_at_end(event, text_widget):
    text_widget.insert("end", "\n")
    text_widget.see("end")
    return "break"


def enforce_line_length(event, text_widget):
    index = text_widget.index("insert")
    line, col = map(int, index.split("."))

    start = f"{line}.0"
    end = f"{line}.end"

    line_text = text_widget.get(start, end)

    if len(line_text) > MAX_CHAT_LEN:
        text_widget.delete(f"{line}.{MAX_CHAT_LEN}", end)
        return "break"
    

def build_chat_editor(parent, title, path, default_relative_path):
    frame = tk.LabelFrame(parent, text=title, padx=8, pady=6)
    frame.pack(fill="both", expand=True, padx=10, pady=6)

    scrollbar = tk.Scrollbar(frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    text = tk.Text(
        frame,
        height=8,
        wrap="word",
        undo=True,
        font=("Consolas", 10),
        spacing1=4,
        spacing3=4,
        yscrollcommand=scrollbar.set
    )
    text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text.yview)

    lines = read_chat_file(path, default_relative_path)
    text.insert("1.0", "\n".join(lines))
    highlight_lines(text)

    # 🔒 Enforcements
    text.bind("<Key>", lambda e: enforce_line_length(e, text))
    text.bind("<Return>", lambda e: force_newline_at_end(e, text))

    # 🔁 Highlight only on logical modification
    text.bind(
        "<<Modified>>",
        lambda e: (
            text.edit_modified(False),
            highlight_lines(text)
        )
    )

    return text


def save_chat_settings():
    picking_lines = picking_text.get("1.0", "end").splitlines()
    ingame_lines  = ingame_text.get("1.0", "end").splitlines()

    picking_lines = validate_chat_lines(picking_lines)
    ingame_lines  = validate_chat_lines(ingame_lines)

    save_chat_file(CHAT_PICKING_PATH, picking_lines)
    save_chat_file(CHAT_INGAME_PATH, ingame_lines)


def highlight_lines(text_widget):
    text_widget.tag_configure("even", background="#f7f7f7")
    text_widget.tag_configure("odd", background="#ffffff")

    text_widget.tag_remove("even", "1.0", "end")
    text_widget.tag_remove("odd", "1.0", "end")

    end_line = int(text_widget.index("end-1c").split(".")[0])

    for i in range(1, end_line + 1):
        tag = "even" if i % 2 == 0 else "odd"
        text_widget.tag_add(tag, f"{i}.0", f"{i}.end")


def reset_chat_to_default(text_widget, target_path, default_relative_path):
    lines = read_chat_file(target_path, default_relative_path)

    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", "\n".join(lines))
    highlight_lines(text_widget)


def build_chat_placeholder_guide(parent):
    frame = tk.LabelFrame(
        parent,
        text="Dynamic Parameters",
        padx=8,
        pady=6
    )
    frame.pack(fill="x", padx=10, pady=(6, 10))

    guide_text = (
        "Available keys:\n"
        "  team / opponent_team / map / map_shortform / foc_role\n\n"
        "Usage example:\n"
        "  I'm in {%team%} team.\n"
        "Output:\n"
        "  I'm in Legion team."
    )

    label = tk.Label(
        frame,
        text=guide_text,
        justify="left",
        anchor="w",
        font=("Consolas", 9),
        fg="#CE3030"
    )
    label.pack(fill="x")

# ============================================================
# Text field handler
debounced_firstname_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_account_firstname)
debounced_lastname_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_account_lastname)
debounced_email_domain_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_account_email_domain)
debounced_password_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_account_password)
debounced_prefix_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_username_prefix)
debounced_prefix_count_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_username_prefix_count_start_at)
debounced_postfix_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_username_postfix)
debounced_postfix_count_save = make_debouncer(root, constant.DEBOUNCE_MS, state.set_username_postfix_count_start_at)

WINDOW_WIDTH = 750
WINDOW_HEIGHT = 800

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = screen_width - 10 - WINDOW_WIDTH
y = screen_height - 90 - WINDOW_HEIGHT

root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

left_frame = tk.Frame(main_frame)
left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
left_frame.rowconfigure(0, weight=1)

form_frame = tk.Frame(left_frame)
form_frame.pack(fill="x", anchor="n")

spacer = tk.Frame(left_frame)
spacer.pack(fill="both", expand=True)

main_frame.columnconfigure(0, weight=0)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(0, weight=1)

first_name_entry = labeled_entry(form_frame, "First Name", state.get_account_firstname())
last_name_entry = labeled_entry(form_frame, "Last Name", state.get_account_lastname())
prefix_entry = labeled_entry(form_frame, "Prefix (optional)", state.get_username_prefix())
postfix_entry = labeled_entry(form_frame, "Postfix (optional)", state.get_username_postfix())
domain_entry = labeled_entry(form_frame, "Email Domain", state.get_account_email_domain())
email_entry = labeled_entry(form_frame, "Email")
username_entry = labeled_entry(form_frame, "Username")
password_entry = labeled_entry(form_frame, "Password", state.get_account_password())

vcmd_int = root.register(validate_int_only)

game_exe_var = tk.StringVar(value=state.get_game_executable())
exe_header = tk.Frame(form_frame)
exe_header.pack(fill="x", pady=(8, 0))

tk.Label(
    exe_header,
    text="Game Launcher"
).pack(side="left")

tk.Button(
    exe_header,
    text="Browse",
    command=on_browse_executable,
    width=10
).pack(side="right")

exe_entry = tk.Entry(
    form_frame,
    textvariable=game_exe_var,
    state="readonly"
)
exe_entry.pack(fill="x", pady=(4, 0))

tk.Button(
    form_frame,
    text="Generate Username & Email",
    command=on_generate
).pack(fill="x", pady=6)

action_row = tk.Frame(form_frame)
action_row.pack(fill="x", pady=6)

tk.Button(
    action_row,
    text="Sign Up",
    command=on_submit,
    width=12
).pack(side="left", expand=True, padx=2)

tk.Button(
    action_row,
    text="Login",
    command=on_login_only,
    width=12
).pack(side="left", expand=True, padx=2)

tk.Button(
    form_frame,
    text="Sign up and run once",
    command=on_signup_and_run_once
).pack(fill="x", pady=4)

status_frame = tk.LabelFrame(left_frame, text="Endless Mode Status")
status_frame.pack(fill="x", side="bottom", pady=10)

tk.Checkbutton(
    status_frame,
    text="Auto start Endless Mode on launch",
    variable=auto_start_endless_var,
    command=on_auto_start_checkbox_changed
).pack(anchor="w", pady=(2, 4))

countdown_label = tk.Label(
    status_frame,
    textvariable=auto_start_countdown_var,
    fg="orange"
)
countdown_label.pack(anchor="w")

duration_label = tk.Label(status_frame, textvariable=duration_var)
duration_label.pack(anchor="w")

iteration_label = tk.Label(status_frame, textvariable=iteration_var)
iteration_label.pack(anchor="w")

start_endless_btn = tk.Button(
    status_frame,
    text="Start Endless Mode",
    command=on_start_endless_mode,
    fg="black"
)
start_endless_btn.pack(fill="x", pady=6)


right_frame = tk.Frame(main_frame)
right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

notebook = ttk.Notebook(right_frame)
notebook.pack(fill="both", expand=True)

extra_settings_tab = tk.Frame(notebook)
logs_tab = tk.Frame(notebook)
chat_settings_tab = tk.Frame(notebook)

# ============================================================
# EXTRA SETTINGS TAB
# ============================================================
notebook.add(extra_settings_tab, text="Extra Settings")

# ============================================================
account_verification_frame = tk.LabelFrame(
    extra_settings_tab,
    text="Account Verification Settings",
    padx=10,
    pady=8
)
account_verification_frame.pack(
    fill="x",
    padx=10,
    pady=10,
    anchor="n"
)

verification_row = tk.Frame(account_verification_frame)
verification_row.pack(anchor="w", pady=4)

tk.Checkbutton(
    verification_row,
    text="Auto Email Verification",
    variable=auto_email_verification_var,
    command=on_auto_email_verification_changed
).grid(row=0, column=0, sticky="w", padx=(0, 20))

tk.Checkbutton(
    verification_row,
    text="Auto Mobile Verification",
    variable=auto_mobile_verification_var,
    command=on_auto_mobile_verification_changed
).grid(row=0, column=1, sticky="w")

# ============================================================
app_settings_frame = tk.LabelFrame(
    extra_settings_tab,
    text="Application Settings",
    padx=10,
    pady=8
)
app_settings_frame.pack(
    fill="x",
    padx=10,
    pady=10,
    anchor="n"
)

app_settings_row = tk.Frame(app_settings_frame)
app_settings_row.pack(anchor="w", pady=4)

tk.Checkbutton(
    app_settings_row,
    text="Auto Updates",
    variable=auto_update_var,
    command=on_auto_update_changed
).grid(row=0, column=0, sticky="w", padx=(0, 20))

tk.Checkbutton(
    app_settings_row,
    text="Auto Restart PC on DNS Failure",
    variable=auto_restart_dns_var,
    command=lambda: state.set_auto_restart_dns(auto_restart_dns_var.get())
).grid(row=0, column=1, sticky="w")

app_settings_row2 = tk.Frame(app_settings_frame)
app_settings_row2.pack(anchor="w", pady=4)

tk.Checkbutton(
    app_settings_row2,
    text="Settings for Slower PC",
    variable=settings_for_slower_pc_var,
    command=lambda: state.set_settings_for_slower_pc(settings_for_slower_pc_var.get())
).grid(row=0, column=0, sticky="w", padx=(0, 20))

tk.Checkbutton(
    app_settings_row2,
    text="Use Ragequit Mode",
    variable=is_ragequit_mode_enabled_var,
    command=lambda: state.set_is_ragequit_mode_enabled(is_ragequit_mode_enabled_var.get()),
    fg="red"
).grid(row=0, column=1, sticky="w")

# ============================================================
username_settings_frame = tk.LabelFrame(
    extra_settings_tab,
    text="Username Generation Settings",
    padx=10,
    pady=8
)

username_settings_frame.pack(
    fill="x",
    padx=10,
    pady=10,
    anchor="n"
)

# ---- Row 1: Checkboxes ----
username_settings_row = tk.Frame(username_settings_frame)
username_settings_row.pack(anchor="w", pady=4)

tk.Checkbutton(
    username_settings_row,
    text="Add count on Prefix",
    variable=add_prefix_count_var,
    command=lambda: on_prefix_checkbox_toggle()
).grid(row=0, column=0, sticky="w", padx=5)

tk.Checkbutton(
    username_settings_row,
    text="Add count on Postfix",
    variable=add_postfix_count_var,
    command=lambda: on_postfix_checkbox_toggle()
).grid(row=0, column=1, sticky="w", padx=5)

# ---- Row 2: Start count inputs ----
username_prefix_postfix_count_row = tk.Frame(username_settings_frame)
username_prefix_postfix_count_row.pack(anchor="w", pady=4)

tk.Label(
    username_prefix_postfix_count_row,
    text="Prefix count start at"
).grid(row=0, column=0, sticky="w", padx=5)

prefix_count_entry = tk.Entry(
    username_prefix_postfix_count_row,
    textvariable=prefix_count_start_var,
    width=6,
    state="disabled",
    validate="key",
    validatecommand=(vcmd_int, "%P")
)
prefix_count_entry.grid(row=0, column=1, padx=5)

tk.Label(
    username_prefix_postfix_count_row,
    text="Postfix count start at"
).grid(row=0, column=2, sticky="w", padx=10)

postfix_count_entry = tk.Entry(
    username_prefix_postfix_count_row,
    textvariable=postfix_count_start_var,
    width=6,
    state="disabled",
    validate="key",
    validatecommand=(vcmd_int, "%P")
)
postfix_count_entry.grid(row=0, column=3, padx=5)

# ============================================================
# CHAT TAB
# ============================================================
notebook.add(chat_settings_tab, text="Chat Settings")

build_chat_placeholder_guide(chat_settings_tab)

CHAT_PICKING_PATH = get_chat_path("chat_picking.txt")
CHAT_INGAME_PATH  = get_chat_path("chat_ingame.txt")

picking_text = build_chat_editor(
    chat_settings_tab,
    "Picking Phase Chat",
    CHAT_PICKING_PATH,
    default_relative_path="data/chat_picking.txt"
)
ingame_text = build_chat_editor(
    chat_settings_tab,
    "In-Game Chat",
    CHAT_INGAME_PATH,
    default_relative_path="data/chat_ingame.txt"
)

tk.Button(
    chat_settings_tab,
    text="Save Chat Settings",
    command=save_chat_settings
).pack(pady=10)


# ============================================================
# LOGS TAB
# ============================================================
notebook.add(logs_tab, text="Logs")

log_text = tk.Text(
    logs_tab,
    bg="black",
    fg="lime",
    font=("Consolas", 9),
    state="disabled"
)
log_text.pack(fill="both", expand=True)

log_text.tag_configure("INFO", foreground="lime")
log_text.tag_configure("WARN", foreground="orange")
log_text.tag_configure("ERROR", foreground="red")

notebook.select(logs_tab)

style = ttk.Style()
style.theme_use("default")

# ============================================================
poll_log_queue()
exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))
on_prefix_checkbox_toggle()
on_postfix_checkbox_toggle()

# ============================================================
first_name_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_firstname_save(
        first_name_entry.get().strip()
    )
)

last_name_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_lastname_save(
        last_name_entry.get().strip()
    )
)

prefix_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_prefix_save(
        prefix_entry.get().strip()
    )
)

postfix_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_postfix_save(
        postfix_entry.get().strip()
    )
)

domain_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_email_domain_save(
        domain_entry.get().strip()
    )
)

password_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_password_save(
        password_entry.get().strip()
    )
)

prefix_count_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_prefix_count_save(
        prefix_count_entry.get().strip()
    )
)

postfix_count_entry.bind(
    "<KeyRelease>",
    lambda e: debounced_postfix_count_save(
        postfix_count_entry.get().strip()
    )
)

# ============================================================
# AUTO START ENDLESS MODE (DELAYED & CANCELLABLE)
# ============================================================

if auto_start_endless_var.get():
    try_auto_start_from_config()

if __name__ == "__main__":
    set_self_high_priority()
    root.mainloop()