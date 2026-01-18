
import requests
import utilities.constants as constant
import core.state as state
import time
import re
import socket
import subprocess
import threading
import sys

from utilities.loggerSetup import setup_logger
from utilities.ipAddressGenerator import random_public_ip
from urllib.parse import urlencode
from requests.exceptions import ConnectionError, Timeout
from http.client import RemoteDisconnected
from requests.exceptions import RequestException
from utilities.accountVerification import AccountVerifier

# Initialize Logger
logger = setup_logger()

# Main Function
def signup_user(first_name, last_name, email, username, password):
    session = requests.Session()
    session.headers.update({
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "Chrome/143.0.0.0"
        )
    })

    try:
        # 1️⃣ GET signup page
        resp = safe_get(session, constant.SIGNUP_URL, restart_on_dns=state.get_auto_restart_dns())
        resp.raise_for_status()

        match = re.search(r'name="_csrf"\s+value="([^"]+)"', resp.text)
        if not match:
            logger.error("[ERROR] Failed to get CSRF token.")
            return False, "CSRF not found"

        csrf = match.group(1)

        fakeIp = random_public_ip()

        payload = {
            "_csrf": csrf,
            "User[first_name]": first_name,
            "User[last_name]": last_name,
            "User[email]": email,
            "User[display_name]": first_name,
            "User[username]": username,
            "User[password]": password,
            "User[repeat_password]": password,
            "User[role_id]": "player",
            "User[timezone_id]": 1,
            "User[ip_address]": fakeIp,
            "User[status_id]": 1,
            "User[user_referral_code]": "",
            "User[send_sms]": 1,
            "User[reCaptcha]": "",
            "g-recaptcha-response": "",
        }

        raw_body = urlencode(payload)

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": constant.BASE_URL,
            "referer": constant.SIGNUP_URL,
            "x-csrf-token": csrf,
            "x-requested-with": "XMLHttpRequest",
        }

        # 4️⃣ POST signup
        r = session.post(
            constant.SIGNUP_URL,
            headers=headers,
            data=raw_body,
            timeout=15,
        )

        success, msg = is_signup_success(r)

        if success:
            logger.info(f"[INFO] Account {username} created")
            logger.info(f"[INFO] Password: {password}")
            state.INGAME_STATE.setUsername(username)
            state.INGAME_STATE.setPassword(password)
            log_username(username)

            if state.get_auto_email_verification() or state.get_auto_mobile_verification():
                start_account_verification_async(username)

            return True, msg
        else:
            #logger.info(f"[ERROR] Failed to create account {username}: due to username existed or duplicated email used.")
            logger.info(f"[DEBUG] Raw response: {r.text}")
            return False, msg       

    except (ConnectionError, Timeout, RemoteDisconnected) as e:
        logger.warning(f"[NET] Signup dropped by server: {e}")
        return False, "connection_dropped"
    
    except RequestException as e:
        logger.error(f"[NETWORK_ERROR] Signup dropped by server: {e}")
        return False, "Network error (DNS / connection failed)"

    except Exception as e:
        logger.exception("[FATAL] Unexpected signup error")
        return False, str(e)
    
def safe_get(
    session,
    url,
    retries=3,
    delay=3,
    restart_on_dns=False  # 🔥 toggle flag
):
    last_exception = None

    for i in range(retries):
        try:
            return session.get(url, timeout=15)

        except Exception as e:
            last_exception = e
            logger.warning(
                f"[RETRY] GET failed ({i+1}/{retries}): {e}"
            )

            # Immediate escalation if DNS issue
            if is_dns_error(e):
                logger.error("[NETWORK] DNS resolution failure detected")

                if restart_on_dns:
                    restart_windows(reason=str(e))

                break  # do not keep retrying DNS failures

            time.sleep(delay)

    raise RuntimeError(
        "DNS resolution failed after retries"
        if is_dns_error(last_exception)
        else "HTTP GET failed after retries"
    )

def is_signup_success(r):
    try:
        data = r.json()
    except ValueError:
        return False, "Invalid JSON response"

    if data.get("status") != "success":
        return False, "Failed to signup: username existed or email used"

    tokens = data.get("tokens", "")
    if "csrf-token" not in tokens:
        return False, "Missing CSRF token"

    return True, "Signup success"

def log_username(username, filename="signup_users.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(username + "\n")

def is_dns_error(exc: Exception) -> bool:
    """
    Detect DNS-related failures safely.
    """
    msg = str(exc).lower()

    return (
        isinstance(exc, requests.exceptions.ConnectionError)
        and (
            "getaddrinfo failed" in msg
            or "name or service not known" in msg
            or "failed to resolve" in msg
        )
    ) or isinstance(exc, socket.gaierror)

def restart_windows(reason: str = ""):
    """
    Restart Windows immediately.
    """
    logger.critical("[SYSTEM] Restarting Windows due to DNS failure")
    if reason:
        logger.critical(f"[SYSTEM] Reason: {reason}")

    # Force immediate restart
    subprocess.run(
        ["shutdown", "/r", "/t", "0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Hard exit if shutdown is blocked
    sys.exit(1)

def start_account_verification_async(username: str):
    def worker():
        try:
            logger.info(f"[INFO] Starting verification process for {username}")
            verifier = AccountVerifier(logger)
            verifier.run(
                mobile=state.get_auto_mobile_verification(),
                email=state.get_auto_email_verification()
            )
            logger.info(f"[INFO] Account verification completed.")
        except Exception:
            logger.exception("[ERROR] Verification failed")

    threading.Thread(
        target=worker,
        daemon=True
    ).start()