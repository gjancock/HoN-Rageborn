import os

from utilities.loggerSetup import setup_logger

# Initialize Logger
logger = setup_logger()


def hard_exit():
    """
    Emergency hard exit.
    Terminates the entire process immediately.
    """
    try:
        logger.critical("[EMERGENCY] F11 pressed! HARD EXIT.")
    finally:
        os._exit(0)
