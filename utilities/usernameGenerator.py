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

    base = random.choice(WORD_POOL)

    sep_prefix = "_" if prefix else ""
    sep_postfix = "_" if postfix else ""

    # minimum: prefix + (generated 2 chars) + postfix
    min_required_length = (
        len(prefix) +
        len(sep_prefix) +
        2 +                     # at least 2 chars generated
        len(sep_postfix) +
        len(postfix)
    )

    target_length = random.randint(
        max(MIN_USERNAME_LENGTH, min_required_length),
        MAX_USERNAME_LENGTH
    )

    available = (
        target_length -
        len(prefix) -
        len(sep_prefix) -
        len(sep_postfix) -
        len(postfix)
    )

    # Always reserve at least 1 char for base and 1 for suffix
    base_len = min(len(base), max(1, available - 1))
    suffix_len = available - base_len

    # Randomize order: base+suffix OR suffix+base
    if random.choice([True, False]):
        part1 = base[:base_len]
        part2 = generate_random_string(suffix_len)
    else:
        part1 = generate_random_string(suffix_len)
        part2 = base[:base_len]

    generated = part1 + part2

    username = f"{prefix}{sep_prefix}{generated}{sep_postfix}{postfix}"
    return username
