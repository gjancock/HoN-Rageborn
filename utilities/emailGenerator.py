from utilities.usernameGenerator import (
    generate_random_string
)
from utilities.constants import DEFAULT_ACCOUNT_EMAIL_DOMAIN

def generate_email(prefix="", postfix="", domain=DEFAULT_ACCOUNT_EMAIL_DOMAIN, length=12):
    prefix = str(prefix).strip().lower()
    postfix = str(postfix).strip().lower()

    rand = generate_random_string(length, length)
    local = "".join(p for p in [prefix, rand, postfix] if p)

    return f"{local}@{domain}"
