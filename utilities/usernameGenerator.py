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

def generate_random_string(min_len=2, max_len=3):
    length = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


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

    underscoreChance = 0.25
    if random.random() < underscoreChance:
        username = "_".join(parts)
    else:
        username = "".join(parts)

    captilizeChance = 0.45
    if random.random() < captilizeChance:
        username = username.capitalize()

    everyFirstCaptilizeChance = 0.25
    if random.random() < everyFirstCaptilizeChance:
        username = username[0].upper() + username[1:] if username else username

    return username