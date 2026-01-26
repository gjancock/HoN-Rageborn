import logging
import tkinter as tk
import random
import subprocess
import threading
import time
import utilities.constants as constant
import os
import core.state as state
import pyautogui
import time
import subprocess
import keyboard

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
from ui.logic import (
    start_endless_ui_refresh
)
from ui.endless_controller import EndlessController

# logging order matter
import ui.autostart as autostart
from ui.process import set_self_high_priority
from ui.hotkeys import hard_exit
from utilities.threadingException import global_thread_exception_handler
from ui.rageborn_runner import start_rageborn_async, run_rageborn_flow
from ui.ui_actions import (
    get_effective_password,
    on_generate,
)
from ui.cycle_runner import run_cycle, endless_worker
from ui.log_view import poll_log_queue
from ui.ui_handlers import (
    on_login_only,
    on_signup_and_run_once,
    on_submit,
)
from ui.game_launcher import (
    browse_executable,
    launch_game_process,
    validate_game_executable,
)
from ui.ui_widgets import (
    labeled_entry,
    set_endless_mode_ui_running
)
from ui.ui_handlers import (
    on_auto_start_checkbox_changed,
    try_auto_start_from_config,
)
from ui.ui_handlers import (
    on_auto_email_verification_changed,
    on_auto_mobile_verification_changed,
    on_auto_update_changed,
)
from ui.ui_state_sync import (
    on_prefix_checkbox_toggle,
    on_postfix_checkbox_toggle,
    on_prefix_count_changed,
    on_postfix_count_changed,
)
from ui.chat_editor import (
    build_chat_editor,
    build_chat_placeholder_guide,
    save_chat_settings,
    reset_chat_to_default,
)

# ============================================================
# APPLICATION SETTINGS
# ============================================================
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
# UI Application 
# ============================================================
root = tk.Tk()
root.update_idletasks()  # ensure geometry info is ready
root.title(f"{INFO_NAME} v{VERSION}")

keyboard.add_hotkey("F11", hard_exit)

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

def _generate_credentials():
    on_generate(
        prefix_entry=prefix_entry,
        postfix_entry=postfix_entry,
        domain_entry=domain_entry,
        add_prefix_count_var=add_prefix_count_var,
        add_postfix_count_var=add_postfix_count_var,
        prefix_count_start_var=prefix_count_start_var,
        postfix_count_start_var=postfix_count_start_var,
        username_entry=username_entry,
        email_entry=email_entry,
    )


def _read_credentials():
    return (
        username_entry.get(),
        get_effective_password(password_entry),
        first_name_entry.get(),
        last_name_entry.get(),
        email_entry.get(),
    )

def one_full_cycle():
    return run_cycle(
        generate_credentials_cb=_generate_credentials,
        read_credentials_cb=_read_credentials,
        signup_cb=signup_user,
        launch_game_process=lambda: launch_game_process(game_exe_var)
    )

endless_controller = EndlessController(
    lambda: endless_worker(
        is_running_cb=auto_mode_var.get,
        run_cycle_cb=one_full_cycle,
    )
)

def validate_int_only(new_value: str) -> bool:
    if new_value == "":
        return True 
    return new_value.isdigit()


def on_start_endless_mode():
    if endless_controller.is_running():
        return

    auto_mode_var.set(True)
    set_endless_mode_ui_running(start_endless_btn)
    endless_controller.start()


prefix_count_start_var.trace_add("write", lambda *_: on_prefix_count_changed(prefix_count_start_var))
postfix_count_start_var.trace_add("write", lambda *_: on_postfix_count_changed(postfix_count_start_var))


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
    command=lambda: browse_executable(game_exe_var, exe_entry),
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
    command=lambda: on_login_only(
        username_entry=username_entry,
        password_entry=password_entry,
        get_password_cb=get_effective_password,
        start_async_cb=start_rageborn_async,
        launch_game_process=lambda: launch_game_process(game_exe_var)
    ),
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
    command=lambda: on_auto_start_checkbox_changed(
        auto_start_var=auto_start_endless_var,
        root=root,
        countdown_var=auto_start_countdown_var,
        validate_exe_cb=lambda show_error=True: validate_game_executable(
            game_exe_var, show_error
        ),
        on_start_cb=on_start_endless_mode,
        autostart_module=autostart,
    )
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

_prefix_state = {"value": False}
tk.Checkbutton(
    username_settings_row,
    text="Add count on Prefix",
    variable=add_prefix_count_var,
    command=lambda: on_prefix_checkbox_toggle(
        enabled_var=add_prefix_count_var,
        count_var=prefix_count_start_var,
        entry_widget=prefix_count_entry,
        last_enabled_ref=_prefix_state,
    )
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
    command=lambda: save_chat_settings(
        picking_text=picking_text,
        ingame_text=ingame_text,
        picking_path=CHAT_PICKING_PATH,
        ingame_path=CHAT_INGAME_PATH,
    )
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
poll_log_queue(
    root=root,
    log_queue=log_queue,
    log_text=log_text,
    formatter=ui_formatter,
)

start_endless_ui_refresh(
    root,
    duration_var,
    iteration_var,
    interval_ms=1000
)

exe_entry.after(1, lambda: exe_entry.xview_moveto(1.0))
_prefix_state = {"value": False}

add_prefix_count_var.trace_add(
    "write",
    lambda *_: on_prefix_checkbox_toggle(
        enabled_var=add_prefix_count_var,
        count_var=prefix_count_start_var,
        entry_widget=prefix_count_entry,
        last_enabled_ref=_prefix_state,
    )
)

_postfix_state = {"value": False}

add_postfix_count_var.trace_add(
    "write",
    lambda *_: on_postfix_checkbox_toggle(
        enabled_var=add_postfix_count_var,
        count_var=postfix_count_start_var,
        entry_widget=postfix_count_entry,
        last_enabled_ref=_postfix_state,
    )
)


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
    try_auto_start_from_config(
        auto_start_var=auto_start_endless_var,
        root=root,
        countdown_var=auto_start_countdown_var,
        validate_exe_cb=lambda show_error=False: validate_game_executable(
            game_exe_var, show_error
        ),
        on_start_cb=on_start_endless_mode,
        autostart_module=autostart,
    )


if __name__ == "__main__":
    set_self_high_priority() 
    root.mainloop()