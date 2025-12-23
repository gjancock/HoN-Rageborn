import logging
import os
from datetime import date

def rageborn_logger():
    return setup_logger(log_dir="logs/rageborn")

def ragebirth_logger():
    return setup_logger(log_dir="logs/ragebirth")

def setup_logger(    
    log_dir="logs",
    level=logging.INFO
):
    os.makedirs(log_dir, exist_ok=True)
    name = date.now().strftime('%Y-%m-%d')

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
        fmt="%(asctime)s | %(levelname)-8s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Console handler (optional, useful during dev)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
