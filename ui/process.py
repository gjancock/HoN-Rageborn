import psutil
import os
import logging

logger = logging.getLogger("rageborn")

def set_self_high_priority():
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        logger.info("[DEBUG] Python process set to HIGH")

    except psutil.AccessDenied:
        logger.warning("[DEBUG] Access denied – priority unchanged")
        pass

    except Exception as e:
        logger.warning(f"[DEBUG] Failed to set priority: {e}")
        pass