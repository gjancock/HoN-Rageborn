import logging

logger = logging.getLogger("rageborn")

# ============================
# AUTO-START COUNTDOWN STATE
# ============================

auto_start_timer_id = None
auto_start_countdown_id = None
auto_start_remaining = 0

AUTO_START_DELAY_SECONDS = 5


# ============================
# AUTO-START LOGIC
# ============================

def schedule_auto_start(
    *,
    root,
    countdown_var,
    auto_start_enabled_cb,
    on_start_cb,
):
    """
    Schedule auto-start with countdown.
    """
    global auto_start_timer_id, auto_start_remaining

    if auto_start_timer_id is not None:
        return  # already scheduled

    auto_start_remaining = AUTO_START_DELAY_SECONDS
    countdown_var.set(f"Auto start in {auto_start_remaining}…")

    logger.info("[INFO] Auto-start Endless Mode scheduled")

    auto_start_timer_id = True
    _update_countdown(
        root=root,
        countdown_var=countdown_var,
        auto_start_enabled_cb=auto_start_enabled_cb,
        on_start_cb=on_start_cb,
    )


def cancel_auto_start(root, countdown_var):
    """
    Cancel auto-start countdown.
    """
    global auto_start_timer_id, auto_start_countdown_id

    if auto_start_countdown_id is not None:
        root.after_cancel(auto_start_countdown_id)
        auto_start_countdown_id = None

    auto_start_timer_id = None
    countdown_var.set("")

    logger.info("[INFO] Auto-start Endless Mode cancelled")


def _update_countdown(
    *,
    root,
    countdown_var,
    auto_start_enabled_cb,
    on_start_cb,
):
    """
    Internal countdown tick.
    """
    global auto_start_remaining, auto_start_countdown_id, auto_start_timer_id

    if auto_start_remaining <= 0:
        auto_start_timer_id = None
        auto_start_countdown_id = None
        countdown_var.set("")

        if auto_start_enabled_cb():
            logger.info("[INFO] Auto-starting Endless Mode now")
            on_start_cb()
        else:
            logger.info("[INFO] Auto-start aborted (checkbox unchecked)")
        return

    countdown_var.set(f"Auto start in {auto_start_remaining}…")
    auto_start_remaining -= 1

    auto_start_countdown_id = root.after(
        1000,
        lambda: _update_countdown(
            root=root,
            countdown_var=countdown_var,
            auto_start_enabled_cb=auto_start_enabled_cb,
            on_start_cb=on_start_cb,
        )
    )
