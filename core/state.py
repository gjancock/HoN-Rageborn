import threading

STOP_EVENT = threading.Event()

vote_in_progress = threading.Event()
vote_already_cast = threading.Event()
