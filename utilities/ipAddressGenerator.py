import random

def random_public_ip():
    while True:
        ip = [
            random.randint(1, 223),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(1, 254),
        ]

        # Exclude private & reserved ranges
        if ip[0] == 10:
            continue
        if ip[0] == 127:
            continue
        if ip[0] == 169 and ip[1] == 254:
            continue
        if ip[0] == 172 and 16 <= ip[1] <= 31:
            continue
        if ip[0] == 192 and ip[1] == 168:
            continue

        return ".".join(map(str, ip))
