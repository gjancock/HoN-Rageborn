import random
import string

# =========================
# CONFIG
# =========================

MIN_USERNAME_LENGTH = 2
MAX_USERNAME_LENGTH = 16

MIN_SUFFIX_LENGTH = 2
MAX_SUFFIX_LENGTH = 6

UNDERSCORE_WEIGHT = 5     # lower = rarer
NORMAL_CHAR_WEIGHT = 4   # higher = more common

# =========================
# WORD POOLS (REAL-WORLD)
# =========================

WORDS_GAMING = [
    "Shadow", "Ghost", "Rage", "Storm", "Blade",
    "Hunter", "Reaper", "Viper", "Phantom",
    "Titan", "Knight", "Sniper", "Warden",
    "Fury", "Slayer", "Specter", "Riot"
]

WORDS_REAL = [
    "Atlas", "Nova", "Orion", "Apollo", "Echo",
    "Neo", "Zen", "Apex", "Prime", "Vector",
    "Pixel", "Matrix", "Signal", "Orbit"
]

WORDS_TECH = [
    "Byte", "Cipher", "Kernel", "Logic",
    "Quantum", "Syntax", "Binary", "Crypto",
    "Circuit", "Node", "Protocol"
]

WORDS_FANTASY = [
    "Maliken", "Inferno", "Arcane", "Void",
    "Ember", "Abyss", "Rift", "Myth",
    "Legion", "Hellborne", "Vanguard"
]

FIRST_NAMES = [
    "Adam", "Alex", "Aaron", "Ben", "Brian",
    "Chris", "Daniel", "David", "Eric", "Ethan",
    "Jack", "James", "Jason", "John", "Kevin",
    "Lucas", "Mark", "Marcus", "Michael", "Nathan",
    "Oliver", "Ryan", "Samuel", "Sean", "Steven",
    "Thomas", "William"
]

FIRST_NAMES_FEMALE = [
    "Alice", "Alicia", "Amy", "Anna", "Ashley",
    "Catherine", "Emily", "Emma", "Grace", "Hannah",
    "Jessica", "Julia", "Laura", "Linda", "Lucy",
    "Michelle", "Natalie", "Rachel", "Sarah", "Sophia"
]

LAST_NAME_LIKE = [
    "Brown", "Clark", "Davis", "Evans", "Garcia",
    "Harris", "Johnson", "Jones", "Lee", "Lewis",
    "Martin", "Miller", "Moore", "Roberts", "Smith",
    "Taylor", "Walker", "White", "Wilson", "Young"
]

NICKNAME_STYLE = [
    "Ace", "Jay", "Kay", "Lex", "Max",
    "Ray", "Sam", "Tony", "Vic", "Zed"
]

WORD_POOL = (
    WORDS_GAMING +
    WORDS_REAL +
    WORDS_TECH +
    WORDS_FANTASY +
    FIRST_NAMES +
    FIRST_NAMES_FEMALE +
    LAST_NAME_LIKE +
    NICKNAME_STYLE
)

# =========================
# RANDOM STRING
# =========================

def generate_random_string(length):
    normal_chars = (
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits
    )

    weighted_chars = (
        normal_chars * NORMAL_CHAR_WEIGHT +
        "_" * UNDERSCORE_WEIGHT
    )

    return ''.join(random.choices(weighted_chars, k=length))

# =========================
# WORD-BASED USERNAME
# =========================

def generate_word_username(prefix="", postfix=""):
    prefix = prefix.strip()
    postfix = postfix.strip()

    sep_prefix = "_" if prefix else ""
    sep_postfix = "_" if postfix else ""

    fixed_length = (
        len(prefix) +
        len(sep_prefix) +
        len(sep_postfix) +
        len(postfix)
    )

    # 🔒 HARD SAFETY: prefix/postfix too long
    if fixed_length >= MAX_USERNAME_LENGTH:
        # preserve prefix/postfix, trim safely if needed
        result = f"{prefix}{sep_prefix}{sep_postfix}{postfix}"
        return result[:MAX_USERNAME_LENGTH]

    # space available for generated content
    available = MAX_USERNAME_LENGTH - fixed_length

    # ensure at least 1 char generated
    available = max(1, available)

    # choose random total length safely
    target_length = random.randint(
        MIN_USERNAME_LENGTH,
        fixed_length + available
    )

    generated_space = target_length - fixed_length

    # choose base + suffix split
    base = random.choice(WORD_POOL)

    base_len = min(len(base), max(1, generated_space - 1))
    suffix_len = generated_space - base_len

    # allow generated part to start with number or underscore
    if random.choice([True, False]):
        generated = base[:base_len] + generate_random_string(suffix_len)
    else:
        generated = generate_random_string(suffix_len) + base[:base_len]

    username = f"{prefix}{sep_prefix}{generated}{sep_postfix}{postfix}"
    return username
