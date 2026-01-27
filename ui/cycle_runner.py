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

    username = None
    password = None

    try:
        # --------------------------------------------------
        # 1️⃣ Resolve account (pending OR new)
        # --------------------------------------------------
        while not state.STOP_EVENT.is_set():

            pending = state.get_latest_pending_account()

            if pending:
                logger.info(f"[CYCLE] Using pending account: {pending.username}")
                username = pending.username
                password = pending.password
                break  # ✅ do NOT signup again

            # No pending account → create new
            generate_credentials_cb()
            username, password, first, last, email = read_credentials_cb()

            logger.info("-------------------------------------------")
            logger.info(f"[INFO] Generated account: {username}")

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
                time.sleep(random.uniform(1, 3))
                continue

            if success:
                logger.info("[INFO] Signup success!")
                break

            logger.info(f"[INFO] Failed to signup account {username}: {msg}")
            logger.info("[INFO] Regenerating new account")
            time.sleep(random.uniform(1, 3))

        # --------------------------------------------------
        # 2️⃣ Sanity check before launch
        # --------------------------------------------------
        if not username or not password:
            logger.warning("[WARN] Missing credentials before launch, invoking failsafe")

            username, password = _force_generate_account(
                generate_credentials_cb,
                read_credentials_cb,
                signup_cb,
            )

            if not username or not password:
                logger.error("[FATAL] Failsafe account generation failed, skipping cycle")
                return False

        logger.info(f"[INFO] Username {username} launching Rageborn.exe")

        # --------------------------------------------------
        # 3️⃣ Launch Rageborn
        # --------------------------------------------------
        rageborn_runner.run_rageborn_flow(
            username,
            password,
            launch_game_process,
        )

        # --------------------------------------------------
        # 4️⃣ Pending account successfully consumed
        # --------------------------------------------------
        state.clear_pending_account(username)

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


def _force_generate_account(generate_credentials_cb, read_credentials_cb, signup_cb):
    """
    Hard fallback: force-generate a brand new account once.
    """
    logger.warning("[FAILSAFE] Forcing fresh account generation")

    while not state.STOP_EVENT.is_set():
        generate_credentials_cb()
        username, password, first, last, email = read_credentials_cb()

        if not username or not password:
            logger.error("[FAILSAFE] UI returned empty credentials")
            return None, None

        try:
            success, msg = signup_cb(first, last, email, username, password)
            if success:
                break

        except Exception as e:
            logger.exception("[FAILSAFE] Signup exception during forced recovery")
            return None, None

    if not success:
        logger.error(f"[FAILSAFE] Forced signup failed: {msg}")
        return None, None

    logger.info("[FAILSAFE] Forced signup successful")
    return username, password

