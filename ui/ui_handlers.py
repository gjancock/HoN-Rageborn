import logging
from tkinter import messagebox

logger = logging.getLogger("rageborn")


def on_login_only(
    *,
    username_entry,
    password_entry,
    get_password_cb,
    start_async_cb,
    launch_game_process,
):
    user = username_entry.get().strip()
    pwd = get_password_cb(password_entry)

    if not user or not pwd:
        messagebox.showerror("Error", "Username and password are required")
        return

    logger.info(f"[INFO] Logging in with existing account: {user}")
    start_async_cb(user, pwd, launch_game_process)


def on_signup_and_run_once(
    *,
    first_name_entry,
    last_name_entry,
    email_entry,
    username_entry,
    password_entry,
    get_password_cb,
    signup_cb,
    start_async_cb,
    launch_game_process,
):
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = get_password_cb(password_entry)

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_cb(first, last, email, user, pwd)

    if success:
        start_async_cb(user, pwd, launch_game_process)
    else:
        messagebox.showerror("Failed", msg)


def on_submit(
    *,
    first_name_entry,
    last_name_entry,
    email_entry,
    username_entry,
    password_entry,
    get_password_cb,
    signup_cb,
):
    first = first_name_entry.get()
    last = last_name_entry.get()
    email = email_entry.get()
    user = username_entry.get()
    pwd = get_password_cb(password_entry)

    if not all([first, last, email, user, pwd]):
        messagebox.showerror("Error", "All fields are required")
        return

    success, msg = signup_cb(first, last, email, user, pwd)

    if success:
        logger.info("[INFO] Signup successful!")
    else:
        logger.error(f"[ERROR] Signup failed: {msg}")


def on_auto_start_checkbox_changed(
    *,
    auto_start_var,
    root,
    countdown_var,
    validate_exe_cb,
    on_start_cb,
    autostart_module,
):
    value = auto_start_var.get()
    import core.state as state
    state.set_auto_start_endless(value)

    if value:
        if not validate_exe_cb():
            auto_start_var.set(False)
            state.set_auto_start_endless(False)
            autostart_module.cancel_auto_start(root, countdown_var)
            return

        autostart_module.schedule_auto_start(
            root=root,
            countdown_var=countdown_var,
            auto_start_enabled_cb=auto_start_var.get,
            on_start_cb=on_start_cb,
        )
    else:
        autostart_module.cancel_auto_start(root, countdown_var)


def try_auto_start_from_config(
    *,
    auto_start_var,
    root,
    countdown_var,
    validate_exe_cb,
    on_start_cb,
    autostart_module,
):
    if not auto_start_var.get():
        return

    if not validate_exe_cb(show_error=False):
        import core.state as state
        state.set_auto_start_endless(False)
        auto_start_var.set(False)
        return

    autostart_module.schedule_auto_start(
        root=root,
        countdown_var=countdown_var,
        auto_start_enabled_cb=auto_start_var.get,
        on_start_cb=on_start_cb,
    )


def on_auto_email_verification_changed(var):
    import core.state as state
    state.set_auto_email_verification(var.get())


def on_auto_mobile_verification_changed(var):
    import core.state as state
    state.set_auto_mobile_verification(var.get())


def on_auto_update_changed(var):
    import core.state as state
    state.set_auto_update(var.get())


def on_username_prefix_add_count_changed(var):
    import core.state as state
    state.set_username_prefix_count_enabled(var.get())


def on_username_postfix_add_count_changed(var):
    import core.state as state
    state.set_username_postfix_count_enabled(var.get())
