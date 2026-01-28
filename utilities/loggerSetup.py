import logging
from datetime import date
from utilities.paths import LOG_DIR

#
LOGGER_NAME = "rageborn"

def setup_logger(
    *,
    level=logging.INFO,
    ui_queue=None
):
    LOG_DIR.mkdir(exist_ok=True)

    log_file = LOG_DIR / f"{date.today().strftime('%d-%m-%Y')}.log"

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if ui_queue is not None:
        from logging.handlers import QueueHandler
        logger.addHandler(QueueHandler(ui_queue))

    logger.propagate = False
    return logger


def setup_ocr_logger():
    logger = logging.getLogger("OCR")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # prevent duplicate handlers

    log_file = LOG_DIR / "ocr.log"

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        "%H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False  # 🔴 VERY IMPORTANT

    return logger

