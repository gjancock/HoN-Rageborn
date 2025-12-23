import logging
import os
from datetime import date

class TkLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        self.log_queue.put(msg)

def setup_logger(    
    log_dir="logs",
    level=logging.INFO,
    ui_queue=None
):
    os.makedirs(log_dir, exist_ok=True)
    name = date.today().strftime("%d-%m-%Y")

    log_file = os.path.join(
        log_dir,
        f"{name}.log"
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers (important!)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        #fmt="%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s", # default
        datefmt="%H:%M:%S"
    )

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Tkinter handler (optional)
    if ui_queue:
        th = TkLogHandler(ui_queue)
        th.setFormatter(formatter)
        logger.addHandler(th)

    return logger
