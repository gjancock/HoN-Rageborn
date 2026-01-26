import threading
import random

from utilities.config import write_config_bool, write_config_str
from datetime import datetime

class InGameState:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_map = ""
        self._current_team = ""
        self._username = ""
        self._password = ""
        self._position = 0
        self._focRole = ""
        self._isAfk = False
        self._isRageQuitInitiated = False

    def setCurrentMap(self, map):
        with self._lock:
            self._current_map = map

    def setCurrentTeam(self, team):
        with self._lock:
            self._current_team = team

    def setUsername(self, username):
        with self._lock:
            self._username = username

    def setPassword(self, password):
        with self._lock:
            self._password = password

    def setPosition(self, position):
        with self._lock:
            self._position = position

    def setFocRole(self, role):
        with self._lock:
            self._focRole = role

    def setIsAfk(self, isAfk):
        with self._lock:
            self._isAfk = isAfk

    def setIsRageQuitInitiated(self, isRageQuitInitiated):
        with self._lock:
            self._isRageQuitInitiated = isRageQuitInitiated

    def getCurrentMap(self):
        with self._lock:
            return self._current_map
        
    def getCurrentTeam(self):
        with self._lock:
            return self._current_team
        
    def getUsername(self):
        with self._lock:
            return self._username
        
    def getPassword(self):
        with self._lock:
            return self._password
        
    def getPosition(self):
        with self._lock:
            return self._position
        
    def getFocRole(self):
        with self._lock:
            return self._focRole
        
    def getIsAfk(self):
        with self._lock:
            return self._isAfk
        
    def getIsRageQuitInitiated(self):
        with self._lock:
            return self._isRageQuitInitiated

#
CRASH_EVENT = threading.Event()
STOP_EVENT = threading.Event()
SCAN_VOTE_EVENT = threading.Event()
SCAN_LOBBY_MESSAGE_EVENT = threading.Event()

# =========================
# CONFIG-DRIVEN STATES
# =========================
AUTO_START_ENDLESS = False
AUTO_EMAIL_VERIFICATION = False
AUTO_MOBILE_VERIFICATION = False
AUTO_RESTART_DNS = False
AUTO_UPDATE = True
SLOWER_PC_MODE = False
RAGEQUIT_MODE = False
GAME_EXECUTABLE = ""
USERNAME_PREFIX = ""
USERNAME_POSTFIX = ""
ACCOUNT_FIRSTNAME = ""
ACCOUNT_LASTNAME = ""
ACCOUNT_PASSWORD = ""
ACCOUNT_EMAIL_DOMAIN = ""
USERNAME_PREFIX_COUNT_ENABLED = False
USERNAME_POSTFIX_COUNT_ENABLED = False
USERNAME_PREFIX_COUNT_START_AT = 1
USERNAME_POSTFIX_COUNT_START_AT = 1

#
INGAME_STATE = InGameState() 

#
CURRENT_CYCLE_NUMBER = None
MAX_CYCLE_NUMBER = 3

#
ITERATION_COUNT = 0
AUTO_START_TIME = None

STATE_LOCK = threading.Lock()

def reset_endless_stats():
    global ITERATION_COUNT, AUTO_START_TIME
    with STATE_LOCK:
        ITERATION_COUNT = 0
        AUTO_START_TIME = datetime.now()

def increment_iteration():
    global ITERATION_COUNT
    with STATE_LOCK:
        ITERATION_COUNT += 1

def get_iteration_count():
    with STATE_LOCK:
        return ITERATION_COUNT

def get_elapsed_seconds():
    with STATE_LOCK:
        if AUTO_START_TIME is None:
            return 0
        return int((datetime.now() - AUTO_START_TIME).total_seconds())

def get_auto_start_endless():
    return AUTO_START_ENDLESS

def get_game_executable():
    return GAME_EXECUTABLE

def get_auto_email_verification():
    return AUTO_EMAIL_VERIFICATION

def get_auto_mobile_verification():
    return AUTO_MOBILE_VERIFICATION

def get_auto_restart_dns():
    return AUTO_RESTART_DNS

def get_auto_update():
    return AUTO_UPDATE

def get_settings_for_slower_pc():
    return SLOWER_PC_MODE

def get_is_ragequit_mode_enabled():
    return RAGEQUIT_MODE

def get_username_prefix():
    return USERNAME_PREFIX

def get_username_postfix():
    return USERNAME_POSTFIX

def get_account_firstname():
    return ACCOUNT_FIRSTNAME

def get_account_lastname():
    return ACCOUNT_LASTNAME

def get_account_email_domain():
    return ACCOUNT_EMAIL_DOMAIN

def get_account_password():
    return ACCOUNT_PASSWORD

def get_username_prefix_count_enabled():
    return USERNAME_PREFIX_COUNT_ENABLED

def get_username_postfix_count_enabled():
    return USERNAME_POSTFIX_COUNT_ENABLED

def get_username_prefix_count_start_at():
    return USERNAME_PREFIX_COUNT_START_AT

def get_username_postfix_count_start_at():
    return USERNAME_POSTFIX_COUNT_START_AT

def set_auto_start_endless(value: bool):
    global AUTO_START_ENDLESS
    AUTO_START_ENDLESS = value
    write_config_bool("endless", "auto_start", value)

def set_game_executable(executable_path: str):
    global GAME_EXECUTABLE
    GAME_EXECUTABLE = executable_path
    write_config_str("paths", "game_executable", executable_path)

def set_auto_email_verification(value: bool):
    global AUTO_EMAIL_VERIFICATION
    AUTO_EMAIL_VERIFICATION = value
    write_config_bool("verification", "auto_email", value)

def set_auto_mobile_verification(value: bool):
    global AUTO_MOBILE_VERIFICATION
    AUTO_MOBILE_VERIFICATION = value
    write_config_bool("verification", "auto_mobile", value)

def set_auto_restart_dns(value: bool):
    global AUTO_RESTART_DNS
    AUTO_RESTART_DNS = value
    write_config_bool("network", "auto_restart_dns", value)

def set_auto_update(value: bool):
    global AUTO_UPDATE
    AUTO_UPDATE = value
    write_config_bool("settings", "auto_update", value)

def set_settings_for_slower_pc(value: bool):
    global SLOWER_PC_MODE
    SLOWER_PC_MODE = value
    write_config_bool("performance", "slower_pc_mode", value)

def set_is_ragequit_mode_enabled(value: bool):
    global RAGEQUIT_MODE
    RAGEQUIT_MODE = value
    write_config_bool("settings", "ragequit", value)

def set_username_prefix(prefix: str):
    global USERNAME_PREFIX
    USERNAME_PREFIX = prefix
    write_config_str("username_generator", "prefix", prefix)

def set_username_postfix(postfix: str):
    global USERNAME_POSTFIX
    USERNAME_POSTFIX = postfix
    write_config_str("username_generator", "postfix", postfix)

def set_account_firstname(firstname: str):
    global ACCOUNT_FIRSTNAME
    ACCOUNT_FIRSTNAME = firstname
    write_config_str("account", "firstname", firstname)

def set_account_lastname(lastname: str):
    global ACCOUNT_LASTNAME
    ACCOUNT_LASTNAME = lastname
    write_config_str("account", "lastname", lastname)

def set_account_email_domain(email_domain: str):
    global ACCOUNT_EMAIL_DOMAIN
    ACCOUNT_EMAIL_DOMAIN = email_domain
    write_config_str("account", "email_domain", email_domain)

def set_account_password(password: str):
    global ACCOUNT_PASSWORD
    ACCOUNT_PASSWORD = password
    write_config_str("account", "password", password)

def set_username_prefix_count_enabled(value: bool):
    global USERNAME_PREFIX_COUNT_ENABLED
    USERNAME_PREFIX_COUNT_ENABLED = value
    write_config_bool("username_generator", "add_prefix_count", value)

def set_username_postfix_count_enabled(value: bool):
    global USERNAME_POSTFIX_COUNT_ENABLED
    USERNAME_POSTFIX_COUNT_ENABLED = value
    write_config_bool("username_generator", "add_postfix_count", value)

def set_username_prefix_count_start_at(value: int):
    global USERNAME_PREFIX_COUNT_START_AT
    USERNAME_PREFIX_COUNT_START_AT = value
    write_config_str("username_generator", "prefix_count_start", str(value))

def set_username_postfix_count_start_at(value: int):
    global USERNAME_POSTFIX_COUNT_START_AT
    USERNAME_POSTFIX_COUNT_START_AT = value
    write_config_str("username_generator", "postfix_count_start", str(value))

def get_cycle_number():
    return CURRENT_CYCLE_NUMBER

def init_cycle_number():
    """
    Call once when program starts.
    """
    global CURRENT_CYCLE_NUMBER
    if CURRENT_CYCLE_NUMBER is None:
        CURRENT_CYCLE_NUMBER = random.randint(1, MAX_CYCLE_NUMBER)


def next_cycle_number():
    """
    Advance the cycle: 1 → 2 → 3 → 1
    """
    global CURRENT_CYCLE_NUMBER
    if CURRENT_CYCLE_NUMBER is None:
        init_cycle_number()
    else:
        CURRENT_CYCLE_NUMBER += 1
        if CURRENT_CYCLE_NUMBER > MAX_CYCLE_NUMBER:
            CURRENT_CYCLE_NUMBER = 1

    return CURRENT_CYCLE_NUMBER
