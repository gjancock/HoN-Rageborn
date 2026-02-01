import secrets
import string


def generate_password(min_len=8, max_len=10):
    if min_len < 3:
        raise ValueError("Minimum length must be at least 3")

    length = secrets.randbelow(max_len - min_len + 1) + min_len

    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}<>?"

    # ✅ Guarantee required characters
    password_chars = [
        secrets.choice(uppercase),  # 1 uppercase
        secrets.choice(digits),     # 1 number
        secrets.choice(special),    # 1 special
    ]

    # Remaining characters (any allowed)
    remaining_length = length - len(password_chars)
    all_chars = uppercase + lowercase + digits + special

    password_chars.extend(
        secrets.choice(all_chars)
        for _ in range(remaining_length)
    )

    # Shuffle to remove predictable positions
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
