import threading

class InGameState:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_map = ""

    def setCurrentMap(self, map):
        with self._lock:
            self._current_map = map

    def getCurrentMap(self):
        with self._lock:
            return self._current_map

#
STOP_EVENT = threading.Event()
SCAN_VOTE_EVENT = threading.Event()
SCAN_LOBBY_MESSAGE_EVENT = threading.Event()

#
INGAME_STATE = InGameState() # usage: STATE.setCurrentMap("Forest") / STATE.getCurrentMap()

#
vote_in_progress = threading.Event()
vote_already_cast = threading.Event()
