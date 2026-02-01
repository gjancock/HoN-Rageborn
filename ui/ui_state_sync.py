# ui/ui_state_sync.py
import logging
import core.state as state
from utilities.usernameGenerator import (
    reset_prefix_counters,
    reset_postfix_counters,
    set_prefix_counters,
    set_postfix_counters,
)

logger = logging.getLogger("rageborn")


def on_prefix_checkbox_toggle(
    *,
    enabled_var,
    count_var,
    entry_widget,
    last_enabled_ref,
):
    enabled = enabled_var.get()

    if enabled and not last_enabled_ref["value"]:
        count_var.set(1)
        state.set_username_prefix_count_start_at(1)
        reset_prefix_counters()

    entry_widget.config(
        state="normal" if enabled else "disabled"
    )

    state.set_username_prefix_count_enabled(enabled)
    last_enabled_ref["value"] = enabled


def on_postfix_checkbox_toggle(
    *,
    enabled_var,
    count_var,
    entry_widget,
    last_enabled_ref,
):
    enabled = enabled_var.get()

    if enabled and not last_enabled_ref["value"]:
        count_var.set(1)
        state.set_username_postfix_count_start_at(1)
        reset_postfix_counters()

    entry_widget.config(
        state="normal" if enabled else "disabled"
    )

    state.set_username_postfix_count_enabled(enabled)
    last_enabled_ref["value"] = enabled


def on_prefix_count_changed(var):
    try:
        value = var.get()
    except Exception:
        return

    state.set_username_prefix_count_start_at(value)
    set_prefix_counters(value)


def on_postfix_count_changed(var):
    try:
        value = var.get()
    except Exception:
        return

    state.set_username_postfix_count_start_at(value)
    set_postfix_counters(value)

def on_account_spam_creation_checkbox_toggle(
    *,
    enabled_var,
    count_var,
    entry_widget,
    last_enabled_ref,
):
    enabled = enabled_var.get()

    if enabled and not last_enabled_ref["value"]:
        count_var.set(0)
        state.set_account_spam_creation_quantity(0)
        reset_prefix_counters()

    entry_widget.config(
        state="normal" if enabled else "disabled"
    )

    state.set_account_spam_creation_enabled(enabled)
    last_enabled_ref["value"] = enabled

def on_account_spam_quantity_count_changed(var):
    try:
        value = var.get()
    except Exception:
        return

    state.set_account_spam_creation_quantity(value)
