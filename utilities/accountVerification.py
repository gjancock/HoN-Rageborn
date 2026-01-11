import requests
import random
import string
import time
import re
from urllib.parse import urljoin
import time

BASE_URL = "https://api.mail.tm"
JOKEVIO_URL = "https://app.juvio.com"

USERNAME = "rReaper"
PASSWORD = "@Abc12345"
VERIFY_EMAIL = ""

LOGIN_PAGE_URL = f"{JOKEVIO_URL}/site/login"
LOGIN_POST_URL = f"{JOKEVIO_URL}/site/username-login"
P_PAGE_URL = f"{JOKEVIO_URL}/p"

# =========================
# HELPERS
# =========================

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def api(method, path, token=None, **kwargs):
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

def normalize_cookies(session):
    for c in list(session.cookies):
        session.cookies.set(
            c.name,
            c.value,
            domain="app.juvio.com",
            path="/"
        )

# =========================
# SESSION
# =========================

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36"
    )
})

# =========================
# STEP 1 — GET DOMAINS (FIXED)
# =========================

print("[1] Fetching available domains...")

r = api("GET", "/domains")
r.raise_for_status()

data = r.json()

# mail.tm sometimes returns a list, sometimes hydra format
if isinstance(data, list):
    domains = data
elif isinstance(data, dict):
    domains = data.get("hydra:member", [])
else:
    raise RuntimeError("Unexpected domains response format")

if not domains:
    raise RuntimeError("No domains available")

domain = domains[0]["domain"]
print("[+] Selected domain:", domain)


# =========================
# STEP 2 — CREATE MAIL ACCOUNT
# =========================

while True:
    username = random_string()
    VERIFY_EMAIL = f"{username}@{domain}"
    password = PASSWORD

    print("\n[2] Creating account")
    print("Email:", VERIFY_EMAIL)
    print("Password:", password)

    payload = {
        "address": VERIFY_EMAIL,
        "password": password
    }

    r = api("POST", "/accounts", json=payload)
    
    if r.status_code == 201:
        print("[+] Account created")
        break

    print("Account creation failed (trying again in 5s):", r.text)
    time.sleep(5)

# =========================
# STEP 3 — AUTHENTICATE
# =========================

print("\n[3] Authenticating...")

r = api(
    "POST",
    "/token",
    json={"address": VERIFY_EMAIL, "password": password}
)
r.raise_for_status()

token = r.json()["token"]
print("[+] Token acquired")

# Get account verification email send
# =========================
# STEP 1 — GET LOGIN PAGE
# =========================

print("[1] Fetch login page")

r = session.get(LOGIN_PAGE_URL)

csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', r.text)
if not csrf_match:
    raise RuntimeError("CSRF not found on login page")

csrf_html = csrf_match.group(1)

# =========================
# STEP 2 — LOGIN (MANUAL REDIRECT)
# =========================

print("[2] Login POST")

login_payload = {
    "_csrf": csrf_html,
    "NewLoginForm[username]": USERNAME,
    "NewLoginForm[password]": PASSWORD,
}

login_resp = session.post(
    LOGIN_POST_URL,
    data=login_payload,
    allow_redirects=False
)

if login_resp.status_code in (302, 303):
    redirect_url = urljoin(JOKEVIO_URL, login_resp.headers["Location"])
    session.get(redirect_url)

# =========================
# STEP 3 — LOAD /p
# =========================

print("[3] Load /p")

p_resp = session.get(P_PAGE_URL)

u_match = re.search(r"/u/([A-Za-z0-9]+)", p_resp.text)
if not u_match:
    with open("debug_p.html", "w", encoding="utf-8") as f:
        f.write(p_resp.text)
    raise RuntimeError("/u/{code} not found in /p")

u_code = u_match.group(1)
u_url = f"{JOKEVIO_URL}/u/{u_code}"

print("[+] Found short user code:", u_code)

# =========================
# STEP 4 — LOAD /u/{code}
# =========================

print("[4] Load /u/{code}")

u_resp = session.get(u_url)

profile_match = re.search(r'action="/profile\?id=([^"]+)"', u_resp.text)
if not profile_match:
    with open("debug_u.html", "w", encoding="utf-8") as f:
        f.write(u_resp.text)
    raise RuntimeError("profile id not found")

profile_id = profile_match.group(1)
print("[+] Found profile id:", profile_id)

# Extract masked CSRF token from HTML (NOT from cookie)
csrf_match = re.search(
    r'name="csrf-token"\s+content="([^"]+)"',
    u_resp.text
)

if not csrf_match:
    raise RuntimeError("Masked CSRF token not found in page")

csrf_token = csrf_match.group(1)
print("[+] Masked CSRF token extracted")

# =========================
# STEP 5 — NORMALIZE COOKIES
# =========================

normalize_cookies(session)

csrf_cookie = session.cookies.get("_csrf")
if not csrf_cookie:
    raise RuntimeError("_csrf cookie missing")

# =========================
# STEP 6 — SEND VERIFY EMAIL
# =========================

print("[5] Send verification email")

headers = {
    "Accept": "*/*",
    "Origin": JOKEVIO_URL,
    "Referer": f"{JOKEVIO_URL}/u/{u_code}",
    "X-CSRF-Token": csrf_token,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

payload = {
    "_csrf": csrf_token,
    "VerifyEmailForm[email]": VERIFY_EMAIL
}

resp = session.post(
    f"{JOKEVIO_URL}/user/send-verify-email",
    params={"id": profile_id},
    headers=headers,
    data=payload
)

print("Status:", resp.status_code)
print(resp.text)

# Mail fetching and verification
# =========================
# STEP 4 — WAIT FOR EMAIL (FIXED)
# =========================

print("\n[4] Waiting for incoming email...")
print("➡️  Now manually send the verification email")
print("➡️  Target:", VERIFY_EMAIL)

message_id = None

for attempt in range(60):  # ~60 seconds
    r = api("GET", "/messages", token=token)
    r.raise_for_status()

    data = r.json()

    # mail.tm may return list OR hydra format
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        messages = data.get("hydra:member", [])
    else:
        raise RuntimeError("Unexpected messages response format")

    if messages:
        msg = messages[0]
        message_id = msg["id"]

        print("[+] Email received!")
        print("From:", msg["from"]["address"])
        print("Subject:", msg["subject"])
        break

    print("...waiting")
    time.sleep(3)

if not message_id:
    raise RuntimeError("No email received within timeout")

# =========================
# STEP 5 — FETCH FULL MESSAGE
# =========================

print("\n[5] Fetching full email content...")

r = api("GET", f"/messages/{message_id}", token=token)
r.raise_for_status()

msg = r.json()

# 1️⃣ Try HTML body first
verify_link = None

html_parts = msg.get("html") or []
if isinstance(html_parts, list):
    for part in html_parts:
        matches = re.findall(
            r'https://app\.juvio\.com/verify-email\?[^\s"<>]+',
            part,
            flags=re.IGNORECASE
        )
        if matches:
            verify_link = matches[0]

# 2️⃣ Fallback to plain text
text = msg.get("text", "")
matches = re.findall(
    r'https://app\.juvio\.com/verify-email\?[^\s"<>]+',
    text,
    flags=re.IGNORECASE
)
if matches:
    verify_link = matches[0]

if not verify_link:
    raise RuntimeError("Verification link not found in email")

print("[+] Verification link found:")
print(verify_link)

print("[*] Verifying account...")

verify_resp = requests.get(
    verify_link,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/143.0.0.0 Safari/537.36"
        )
    },
    timeout=15,
    allow_redirects=True
)

print("[VERIFY STATUS]", verify_resp.status_code)

if verify_resp.status_code == 200:
    print("[✅ SUCCESS] Account verified")
else:
    print("[⚠️ WARNING] Verify request returned non-200")
