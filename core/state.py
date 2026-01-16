import threading
import random

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
