# ui/cycle_runner.py
import time
import random
import logging
import core.state as state
from ui import rageborn_runner

logger = logging.getLogger("rageborn")


def run_cycle(
    *,
    generate_credentials_cb,
    read_credentials_cb,
    signup_cb,
    launch_game_process,
):
    """
    One full signup + rageborn cycle.
    No Tk imports. No UI globals.
    """

    try:
        while not state.STOP_EVENT.is_set():
            # 1️⃣ Generate credentials (UI callback)
            generate_credentials_cb()

            # 2️⃣ Read credentials (UI callback)
            username, password, first, last, email = read_credentials_cb()

            logger.info("-------------------------------------------")
            logger.info(f"[INFO] Generated account: {username}")

            # 3️⃣ Signup attempt
            try:
                success, msg = signup_cb(
                    first,
                    last,
                    email,
                    username,
                    password,
                )
            except Exception as e:
                logger.warning(f"[WARN] Signup exception, regenerating: {e}")
                success = False
                msg = "exception"

            if success:
                break

            logger.info(
                f"[INFO] Failed to signup account {username}: {msg}"
            )
            logger.info("[INFO] Regenerating new account")
            time.sleep(random.uniform(1, 3))

        logger.info("[INFO] Signup success!")
        logger.info(f"[INFO] Username {username} launching Rageborn.exe")

        rageborn_runner.run_rageborn_flow(
            username,
            password,
            launch_game_process,
        )

        return True

    except Exception:
        logger.exception("[WARN] Cycle error, recovering")
        time.sleep(10)
        raise

def endless_worker(
    *,
    is_running_cb,
    run_cycle_cb,
):
    logger.info("[INFO] --Endless mode started--")

    while is_running_cb():
        try:
            run_cycle_cb()
            state.increment_iteration()
        except Exception:
            logger.exception("[FATAL] Cycle crashed, recovering")
            time.sleep(10)

    logger.info("[INFO] Endless mode stopped")
