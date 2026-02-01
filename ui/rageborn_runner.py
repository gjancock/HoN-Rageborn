# ui/rageborn_runner.py
import threading
import subprocess
import time
import logging
import pyautogui
import core.state as state
import random

from utilities.accountGenerator import generatePendingAccount
from utilities.common import interruptible_wait

logger = logging.getLogger("rageborn")


def reset_state():
    state.STOP_EVENT.clear()
    state.CRASH_EVENT.clear()


def kill_jokevio():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "juvio.exe"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info("[INFO] Jokevio.exe killed")
    except subprocess.CalledProcessError:
        logger.info("[INFO] Intended to kill Jokevio.exe, but it is not running")


def run_rageborn_flow(username, password, launch_game_process):
    """
    Blocking Rageborn execution.
    """
    try:
        isAccountCreationOnly = state.get_account_spam_creation_enabled()

        if isAccountCreationOnly:
            try:
                accountQuantity = int(state.get_account_spam_creation_quantity())
            except (TypeError, ValueError):
                logger.error("[FATAL] Invalid account creation quantity")
                return

            accountCreated = 0

            while not state.STOP_EVENT.is_set():

                # 🔒 Finite vs infinite handling
                if accountQuantity > 0 and accountCreated >= accountQuantity:
                    break

                success = generatePendingAccount()

                if success:
                    accountCreated += 1
                    state.increment_iteration()
                else:
                    logger.warning(
                        f"[WARN] Account creation failed "
                        f"({accountCreated}/{accountQuantity})"
                    )

                interruptible_wait(
                    round(random.uniform(3, 5), 2)
                )

            logger.info(
                f"[INFO] Account creation finished "
                f"({accountCreated}/{accountQuantity})"
            )
        else:
            if not launch_game_process():
                logger.error("[ERROR] Game launch aborted")
                return

            if state.SLOWER_PC_MODE:
                logger.info("[INFO] RAGEBORN slow mode activated.")

            import rageborn  # late import by design

            reset_state()
            rageborn.start(username, password)

            if state.CRASH_EVENT.is_set():
                logger.exception("[FATAL] Rageborn crashed during runtime")
                raise RuntimeError("Rageborn crash detected")

    except pyautogui.FailSafeException:
        logger.info("[SAFETY] FAILSAFE Triggered! Emergency stop.")
        state.STOP_EVENT.set()
        raise

    except Exception:
        logger.exception("[FATAL] Rageborn crashed")
        raise

    finally:
        kill_jokevio()
        logger.info("[MAIN] Rageborn thread exited")


def _rageborn_thread(username, password, launch_game_process):
    try:
        run_rageborn_flow(username, password, launch_game_process)
    except Exception as e:
        logger.error(f"[THREAD-CRASH] {e}")


def start_rageborn_async(username, password, launch_game_process):
    t = threading.Thread(
        target=_rageborn_thread,
        args=(username, password, launch_game_process),
        daemon=True
    )
    t.start()
