import threading
import random

class InGameState:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_map = ""
        self._current_team = ""

    def setCurrentMap(self, map):
        with self._lock:
            self._current_map = map

    def setCurrentTeam(self, team):
        with self._lock:
            self._current_team = team

    def getCurrentMap(self):
        with self._lock:
            return self._current_map
        
    def getCurrentTeam(self):
        with self._lock:
            return self._current_team

#
STOP_EVENT = threading.Event()
SCAN_VOTE_EVENT = threading.Event()
SCAN_LOBBY_MESSAGE_EVENT = threading.Event()

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
