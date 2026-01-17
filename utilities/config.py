import configparser
import os
import sys
import core.state as state
from utilities.constants import DEFAULT_ACCOUNT_EMAIL_DOMAIN, DEFAULT_ACCOUNT_FIRSTNAME, DEFAULT_ACCOUNT_LASTNAME, DEFAULT_ACCOUNT_PASSWORD
from utilities.runtime import runtime_dir

CONFIG_FILE = os.path.join(runtime_dir(), "config.ini")

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        return config

    config.read(CONFIG_FILE)

    # ---- Booleans ----
    state.AUTO_START_ENDLESS = config.getboolean("endless", "auto_start", fallback=False)
    state.AUTO_EMAIL_VERIFICATION = config.getboolean("verification", "auto_email", fallback=False)
    state.AUTO_MOBILE_VERIFICATION = config.getboolean("verification", "auto_mobile", fallback=False)
    state.AUTO_RESTART_DNS = config.getboolean("network", "auto_restart_dns", fallback=False)
    state.SLOWER_PC_MODE = config.getboolean("performance", "slower_pc_mode", fallback=False)
    state.AUTO_UPDATE = config.getboolean("settings", "auto_update", fallback=True)

    # ---- Strings ----
    state.GAME_EXECUTABLE = config.get("paths", "game_executable", fallback="")
    state.ACCOUNT_EMAIL_DOMAIN = config.get("account", "email_domain", fallback=DEFAULT_ACCOUNT_EMAIL_DOMAIN)
    state.ACCOUNT_PASSWORD = config.get("account", "password", fallback=DEFAULT_ACCOUNT_PASSWORD)
    state.ACCOUNT_FIRSTNAME = config.get("account", "firstname", fallback=DEFAULT_ACCOUNT_FIRSTNAME)
    state.ACCOUNT_LASTNAME = config.get("account", "lastname", fallback=DEFAULT_ACCOUNT_LASTNAME)
    state.USERNAME_PREFIX = config.get("username_generator", "prefix", fallback="")
    state.USERNAME_POSTFIX = config.get("username_generator", "postfix", fallback="")

    # ---- Username counter ----
    state.USERNAME_PREFIX_COUNT_ENABLED = config.getboolean(
        "username_generator", "add_prefix_count", fallback=False
    )
    state.USERNAME_POSTFIX_COUNT_ENABLED = config.getboolean(
        "username_generator", "add_postfix_count", fallback=False
    )

    state.USERNAME_PREFIX_COUNT_START_AT = config.getint(
        "username_generator", "prefix_count_start", fallback=1
    )
    state.USERNAME_POSTFIX_COUNT_START_AT = config.getint(
        "username_generator", "postfix_count_start", fallback=1
    )

    return config

