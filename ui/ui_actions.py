# ui/ui_actions.py
import tkinter as tk
import logging
import core.state as state
import utilities.constants as constant

from utilities.usernameGenerator import (
    generate_counter_username,
    generate_word_username,
)
from utilities.emailGenerator import generate_email

logger = logging.getLogger("rageborn")


def get_effective_password(password_entry):
    pwd = password_entry.get().strip()
    return pwd if pwd else state.get_account_password()


def on_generate(
    *,
    prefix_entry,
    postfix_entry,
    domain_entry,
    add_prefix_count_var,
    add_postfix_count_var,
    prefix_count_start_var,
    postfix_count_start_var,
    username_entry,
    email_entry,
):
    prefix = prefix_entry.get().strip()
    postfix = postfix_entry.get().strip()
    domain = domain_entry.get().strip() or constant.DEFAULT_ACCOUNT_EMAIL_DOMAIN

    use_prefix_count = add_prefix_count_var.get()
    use_postfix_count = add_postfix_count_var.get()

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
        username = generate_word_username(prefix, postfix)

    email = generate_email(prefix, postfix, domain)

    username_entry.delete(0, tk.END)
    username_entry.insert(0, username)

    email_entry.delete(0, tk.END)
    email_entry.insert(0, email)
