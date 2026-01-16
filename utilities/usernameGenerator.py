import random
import string

# =========================
# CONFIG
# =========================

MIN_USERNAME_LENGTH = 2
MAX_USERNAME_LENGTH = 16

MIN_SUFFIX_LENGTH = 2
MAX_SUFFIX_LENGTH = 6

# =========================
# WORD POOLS (EXISTING)
# =========================

WORDS_GAMING = [
    "Shadow", "Ghost", "Rage", "Storm", "Blade",
    "Hunter", "Reaper", "Viper", "Phantom",
    "Titan", "Knight", "Sniper", "Warden",
    "Fury", "Slayer", "Specter", "Riot",
    "Dog", "Reborn", "Hon", "Silo"
]

WORDS_REAL = [
    "Atlas", "Nova", "Orion", "Apollo", "Echo",
    "Neo", "Zen", "Apex", "Prime", "Vector",
    "Pixel", "Matrix", "Signal", "Orbit",
    "Google", "Apple", "iPhone", "Silly", "Dumb",
    "Ugly", "Racer", "weed", "lickmyD"
]

WORDS_TECH = [
    "Byte", "Cipher", "Kernel", "Logic",
    "Quantum", "Syntax", "Binary", "Crypto",
    "Circuit", "Node", "Protocol", "RTX5090", "GTX2080",
    "DDR5"
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
    "Thomas", "William", "Edmond", "Wong", "Ong", "Lim", "Tan", "Jay",
    "G", "Gala", "Malboro", "Owen", "Ocean", "Khaw", "Benjamin",
    "Benji", "Jonathan", "Chu", "Teoh", "Maverick", "Salihin",
    "Lee", "Melwin", "Melvin", "Louis", "Breaky", "Piggy",
    "Loo", "Johnson", "Jovin", "Ian", "Eend", "Wilson"
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

random.shuffle(WORD_POOL)
WORD_INDEX = 0

# =========================
# COUNTER STATE (NEW)
# =========================

_current_prefix_count = None
_current_postfix_count = None

# =========================
# HELPERS
# =========================

def generate_random_string(min_len=2, max_len=3):
    length = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# =========================
# EXISTING GENERATOR (UNCHANGED)
# =========================

def generate_word_username(prefix="", postfix=""):
    global WORD_INDEX

    prefix = str(prefix).strip().lower()
    postfix = str(postfix).strip().lower()

    parts = []

    if prefix:
        parts.append(prefix)

    if WORD_POOL:
        base = str(WORD_POOL[WORD_INDEX % len(WORD_POOL)]).lower()
    else:
        base = "user"

    WORD_INDEX += 1

    parts.append(base)

    filler = generate_random_string(2, 3)
    parts.append(filler)

    if postfix:
        parts.append(postfix)

    if random.random() < 0.25:
        username = "_".join(parts)
    else:
        username = "".join(parts)

    if random.random() < 0.45:
        username = username.capitalize()

    return username[:MAX_USERNAME_LENGTH]

# =========================
# NEW: COUNTER-BASED GENERATOR
# =========================

def generate_counter_username(
    prefix="",
    postfix="",
    use_prefix_count=False,
    use_postfix_count=False,
    prefix_start=1,
    postfix_start=1,
):
    """
    Format rules:
    - Prefix count always FIRST
    - Postfix count always LAST
    - Word pool is NOT used
    - Ascending only
    """

    global _current_prefix_count, _current_postfix_count

    # Initialize counters once
    if use_prefix_count and _current_prefix_count is None:
        _current_prefix_count = int(prefix_start)

    if use_postfix_count and _current_postfix_count is None:
        _current_postfix_count = int(postfix_start)

    parts = []

    if use_prefix_count:
        parts.append(str(_current_prefix_count))

    if prefix:
        parts.append(prefix)

    if postfix:
        parts.append(postfix)

    if use_postfix_count:
        parts.append(str(_current_postfix_count))

    username = "".join(parts)

    # Enforce max length
    if len(username) > MAX_USERNAME_LENGTH:
        username = username[:MAX_USERNAME_LENGTH]

    # Increment AFTER generation
    if use_prefix_count:
        _current_prefix_count += 1

    if use_postfix_count:
        _current_postfix_count += 1

    return username, _current_prefix_count, _current_postfix_count

# =========================
# OPTIONAL RESET (UI / ENDLESS MODE)
# =========================

def reset_prefix_counters():
    global _current_prefix_count
    _current_prefix_count = None

def reset_postfix_counters():
    global _current_postfix_count
    _current_postfix_count = None

def set_prefix_counters(value: int):
    global _current_prefix_count
    _current_prefix_count = value

def set_postfix_counters(value: int):
    global _current_postfix_count
    _current_postfix_count = value
