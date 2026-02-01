# utilities/firewall/utils.py

import subprocess
import shutil
import threading
import random
import time
from typing import Literal

from .rules import (
    outbound_block_rule_name,
    outbound_udp_block_rule_name,
)

Direction = Literal["in", "out"]


class FirewallError(RuntimeError):
    pass


def _ensure_netsh():
    if not shutil.which("netsh"):
        raise FirewallError("netsh not available (Windows only)")


def _run(cmd: list[str]):
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ============================================================
# RULE CREATION
# ============================================================

def ensure_outbound_block(app_name: str, exe_path: str):
    _ensure_netsh()

    # Full outbound block (disabled)
    try:
        _run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={outbound_block_rule_name(app_name)}",
            "dir=out",
            "action=block",
            f"program={exe_path}",
            "enable=no",
        ])
    except Exception:
        pass

    # UDP-only outbound block (disabled)
    try:
        _run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={outbound_udp_block_rule_name(app_name)}",
            "dir=out",
            "action=block",
            "protocol=UDP",
            f"program={exe_path}",
            "enable=no",
        ])
    except Exception:
        pass


# ============================================================
# TOGGLE HELPERS
# ============================================================

def _set_rule(app_name: str, rule_name: str, enable: bool):
    _ensure_netsh()

    _run([
        "netsh", "advfirewall", "firewall", "set", "rule",
        f"name={rule_name}",
        "new",
        f"enable={'yes' if enable else 'no'}",
    ])


def block_udp(app_name: str):
    _set_rule(app_name, outbound_udp_block_rule_name(app_name), True)


def unblock_udp(app_name: str):
    _set_rule(app_name, outbound_udp_block_rule_name(app_name), False)


def block_all_outbound(app_name: str):
    _set_rule(app_name, outbound_block_rule_name(app_name), True)


def unblock_all_outbound(app_name: str):
    _set_rule(app_name, outbound_block_rule_name(app_name), False)


# ============================================================
# 🎭 LAG → TIMEOUT SIMULATION (YOU WANT THIS)
# ============================================================

def simulate_lag_timeout(
    app_name: str,
    *,
    lag_phase=(1.5, 2.5),
    total_duration=(5.0, 7.0),
) -> threading.Event:
    """
    Returns an Event that is SET when firewall is fully restored.
    """

    done_event = threading.Event()

    def worker():
        try:
            block_udp(app_name)
            time.sleep(random.uniform(*lag_phase))

            unblock_udp(app_name)
            block_all_outbound(app_name)

            time.sleep(random.uniform(*total_duration))
        finally:
            unblock_udp(app_name)
            unblock_all_outbound(app_name)

            done_event.set()  # 🔔 FIREWALL RESTORED

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()

    return done_event
