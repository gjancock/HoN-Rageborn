import requests
import random
import string
import time
import re
from urllib.parse import urljoin

import core.state as state
from utilities.loggerSetup import setup_logger


# ============================================================
# CONSTANTS
# ============================================================

BASE_URL = "https://api.mail.tm"
JUVIO_URL = "https://app.juvio.com"

LOGIN_PAGE_URL = f"{JUVIO_URL}/site/login"
LOGIN_POST_URL = f"{JUVIO_URL}/site/username-login"
P_PAGE_URL = f"{JUVIO_URL}/p"

TIMEOUT = 20


# ============================================================
# ACCOUNT VERIFIER ENGINE
# ============================================================

class AccountVerifier:
    def __init__(self, logger=None):
        if logger is None:
            raise ValueError("AccountVerifier requires a logger instance")

        self.logger = logger


        # Session is OWNED by this instance
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            )
        })

        # Runtime state
        self.email = None
        self.password = state.INGAME_STATE.getPassword()
        self.token = None
        self.profile_id = None
        self.csrf_token = None
        self.u_code = None

        self.username = state.INGAME_STATE.getUsername()

    # ========================================================
    # UTILITIES
    # ========================================================

    def random_string(self, length=8):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def api(self, method, path, token=None, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Accept"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return requests.request(
            method,
            f"{BASE_URL}{path}",
            headers=headers,
            **kwargs
        )

    # ========================================================
    # MAIL.TM FUNCTIONS
    # ========================================================

    def get_mail_domain(self):
        self.logger.info("[INFO] Performing email verification...")

        r = self.api("GET", "/domains")
        r.raise_for_status()

        data = r.json()
        domains = data if isinstance(data, list) else data.get("hydra:member", [])

        if not domains:
            raise RuntimeError("No mail domains available")

        domain = domains[0]["domain"]
        return domain

    def create_mail_account(self, domain):
        start = time.monotonic()

        while True:
            if time.monotonic() - start >= TIMEOUT:
                raise RuntimeError("Mail account creation timeout")

            username = self.random_string()
            email = f"{username}@{domain}"

            payload = {"address": email, "password": self.password}
            r = self.api("POST", "/accounts", json=payload)

            if r.status_code == 201:
                self.email = email
                return email

            self.logger.info("[INFO] Retrying create mail account...")
            time.sleep(3)

    def authenticate_mail_account(self):
        r = self.api(
            "POST",
            "/token",
            json={"address": self.email, "password": self.password}
        )
        r.raise_for_status()

        self.token = r.json()["token"]
        return self.token

    # ========================================================
    # JUVIO SESSION
    # ========================================================

    def fetch_login_page(self):
        r = self.session.get(LOGIN_PAGE_URL)
        match = re.search(r'name="_csrf"\s+value="([^"]+)"', r.text)

        if not match:
            self.logger.error("[ERROR] CSRF not found on login page")
            raise RuntimeError("CSRF not found on login page")

        return match.group(1)

    def login_to_juvio(self, csrf_html):
        payload = {
            "_csrf": csrf_html,
            "NewLoginForm[username]": self.username,
            "NewLoginForm[password]": self.password,
        }

        resp = self.session.post(
            LOGIN_POST_URL,
            data=payload,
            allow_redirects=False
        )

        if resp.status_code in (302, 303):
            self.session.get(urljoin(JUVIO_URL, resp.headers["Location"]))

    def fetch_user_code(self):
        r = self.session.get(P_PAGE_URL)
        match = re.search(r"/u/([A-Za-z0-9]+)", r.text)

        if not match:
            self.logger.error("[ERROR] User code not found on /p page")
            raise RuntimeError("User code not found")

        return match.group(1)

    def fetch_profile_data(self, u_code):
        url = f"{JUVIO_URL}/u/{u_code}"
        r = self.session.get(url)

        profile_match = re.search(r'action="/profile\?id=([^"]+)"', r.text)
        csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', r.text)

        if not profile_match or not csrf_match:
            self.logger.error("[ERROR] Failed to extract profile data")
            raise RuntimeError("Profile data extraction failed")

        self.profile_id = profile_match.group(1)
        self.csrf_token = csrf_match.group(1)
        self.u_code = u_code

    # ========================================================
    # VERIFICATION
    # ========================================================

    def generate_random_mobile(self):
        code = random.choice(["+60", "+65", "+62", "+66", "+63"])
        number = ''.join(random.choices(string.digits, k=9))
        return code + number, number

    def send_mobile_verification(self):
        self.logger.info("[INFO] Performing mobile verification..")

        full, short = self.generate_random_mobile()

        headers = {
            "X-CSRF-Token": self.csrf_token,
            "X-Requested-With": "XMLHttpRequest",
        }

        payload = {
            "_csrf": self.csrf_token,
            "VerifyMobileForm[mobile_formatted]": short,
            "VerifyMobileForm[mobile]": full,
            "VerifyMobileForm[send_sms]": "1",
        }

        self.session.post(
            f"{JUVIO_URL}/user/send-verify-new-phone",
            params={"id": self.profile_id},
            headers=headers,
            data=payload
        )
        
        self.logger.info("[INFO] Mobile verification completed.")

    def send_verification_email(self):
        headers = {
            "X-CSRF-Token": self.csrf_token,
            "X-Requested-With": "XMLHttpRequest",
        }

        payload = {
            "_csrf": self.csrf_token,
            "VerifyEmailForm[email]": self.email
        }

        self.session.post(
            f"{JUVIO_URL}/user/send-verify-email",
            params={"id": self.profile_id},
            headers=headers,
            data=payload
        )

    def wait_for_verification_email(self):
        self.logger.info("[INFO] Waiting for verification email")

        for _ in range(60):
            r = self.api("GET", "/messages", token=self.token)
            data = r.json()
            msgs = data if isinstance(data, list) else data.get("hydra:member", [])

            if msgs:
                return msgs[0]["id"]

            time.sleep(2)

        self.logger.error("[ERROR] No verification email received")
        raise RuntimeError("No verification email received")

    def fetch_verification_link(self, message_id):
        r = self.api("GET", f"/messages/{message_id}", token=self.token)
        msg = r.json()

        for part in msg.get("html", []):
            match = re.search(r'https://app\.juvio\.com/verify-email\?[^\s"<>]+', part)
            if match:
                return match.group(0)

        self.logger.error("[ERROR] Verification link not found")
        raise RuntimeError("Verification link not found")

    def verify_email_link(self, link):
        requests.get(link, timeout=15)

    # ========================================================
    # ORCHESTRATION
    # ========================================================

    def run(self, mobile=False, email=False):
        if not (mobile or email):
            return

        csrf = self.fetch_login_page()
        self.login_to_juvio(csrf)
        self.fetch_profile_data(self.fetch_user_code())

        if mobile:
            self.send_mobile_verification()

        if email:
            domain = self.get_mail_domain()
            self.create_mail_account(domain)
            self.authenticate_mail_account()
            self.send_verification_email()
            msg_id = self.wait_for_verification_email()
            link = self.fetch_verification_link(msg_id)
            self.verify_email_link(link)
            self.logger.info("[INFO] Email verification completed.")


# ============================================================
# STANDALONE TEST
# ============================================================

# if __name__ == "__main__":
#     logger = setup_logger()
#     verifier = AccountVerifier(logger)
#     verifier.run(mobile=True, email=True)
