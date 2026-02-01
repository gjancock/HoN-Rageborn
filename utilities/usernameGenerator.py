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
    "Dog", "Reborn", "Hon", "Silo",
    "Ace", "Alpha", "Beast", "Clutch", "Core",
    "Crash", "Dead", "Doom", "Elite", "Fatal",
    "Force", "Fury", "Ghost", "God", "Grim",
    "Havoc", "Inferno", "King", "Legend",
    "Lethal", "Lord", "Master", "Meta",
    "Night", "Prime", "Rage", "Rekt",
    "Savage", "Shadow", "Silent", "Slayer",
    "Storm", "Titan", "Ultra", "Venom",
    "Vicious", "Void", "Wild", "Xeno",
    "Abyss", "Ancient", "Arcane", "Bane",
    "Blood", "Chaos", "Creep", "Dagger",
    "Dire", "Echo", "Ember", "Fiend",
    "Frost", "Invoker", "Mana", "Necro",
    "Oracle", "Phantom", "Razor",
    "Shadowfiend", "Spirit", "Spectre",
    "Templar", "Terror", "Void", "Warden",
    "Zeus",
    "Carry", "Challenger", "Clean", "Diff",
    "Elo", "Flash", "Gap", "Godlike",
    "Hyper", "Int", "Lane", "Main",
    "Mechanic", "Mid", "OP", "Outplay",
    "Pentakill", "Precision", "Smurf",
    "Snowball", "Tilt", "Top",
    "Unkillable", "Wave", "Win",
    "Build", "Cracked", "Edit",
    "Fast", "Flick", "Ghost",
    "Laser", "Movement", "OneTap",
    "Peak", "Quick", "Rush",
    "Sweaty", "Turbo", "Zone",
    "90s", "NoScope", "Clip",
    "Assault", "Bullet", "Combat",
    "Deadshot", "Headshot", "Hunter",
    "Kill", "Marksman", "Operator",
    "Ranger", "Recon", "Shooter",
    "Sniper", "Strike", "Suppressor",
    "Tactical", "Trigger", "Warzone"
]

WORDS_PLAYER_USERNAME = [
    "Sorais", "Heffer", "Merv", "Peasant", "Wartype", "Zannir",
    "JMoney", "HOODY", "M0DERN", "Gorgots", "Riquisimo", "Treoke",
    "Ensid", "Moejellini", "Cat", "Jimmeh", "Husken", "Crazyloon",
    "AllanS", "Makanis", "Tilskueren", "Trell", "burcz", "UesleiLopes",
    "Vulka", "Chanklin", "xzachariah", "luckyluke", "madcow28",
    "Kiritok", "Anubis", "Spectrasoul", "GRIEFGOD", "EsthonX",
    "Porkchop", "OhPeng", "Nasi", "Bassan", "Doru", "Maulefar",
    "rangerboy13", "Yagerbomb775", "Riuicsi", "fotzzz", "DougBadass",
    "GetSauced", "BiHan", "Pizdun", "Slieka4", "AlcaponeYou", 
    "Empaler", "CaTnDoG", "itsskia", "BreakyCPK", "Trastamara",
    "Keusz", "Kruzi", "Shifts", "MITD", "Feroci0us", "gjanko", 
    "Monk", "Trastamara", "Psychos", "Simaio", "Dark", "yugen",
    "Bergelius", "Yenvy", "Xinn", "CoreyKillz", "nobadodo1111", "DUNKERSTYLE",
    "Manes", "DokiDoki", "Moondweller", "BooDaga", "HasheM",
    "Inbreddog", "fleese", "Sly69", "FireDog", "RJX", "Rnewton12",
    "EZro", "Daddy", "2LeaN", "FaAmir", "drewmc024", "Requice", "Ouchmouse",
    "JipongYou", "ajcut5", "bluegriffin", "Kruzi", "veenzzero88",
    "Mirock", "zeNAP", "Sarje", "flazepops", "Haz", "lonestar750", 
    "EternalKiss", "Luofeng", "goose", "xopowui17", "nattaporn91",
    "xviralx", "TrashMe", "dew", "mevvtwo", "Onyx711", "masistas", 
    "newEra", "Ritch", "LegendBayby", "doktur", "Pato", "Stevsta",
    "Cr33pyLeo", "hjrdis", "Rico", "RavenArrowz", "gnomskii", "DarkSky",
    "Rehvessori", "iznomis", "zensomo", "Matheusin", "friday13", "Wolfkat",
    "Benzington", "Sommar", "dyadya", "salidron", "PahaTorsti", "arcanemagix",
    "yogi", "Benoit", "Foliarz", "HazeBoy", "Guga", "wtf", "XERO92", "Kongo",
    "Micke", "SmerSBoys", "Fervor", "Cena", "Marius", "Kawaii", "MiTsSs", "Seacow",
    "Ke", "Salt", "Bardiel", "Goston", "Jakjat", "Mallz", "Mikedk7", "Paj",
    "Matthew", "StrenX", "tushycatt", "Zeroxoz", "Skeletonboz", "MorningYew94",
    "Aggamenon", "Asmodai", "Azravos", "BeheResto", "Yoounited",
    "Oloapps19", "HOWiFeed", "Momeantom", "Socknick", "SoNeat", 
    "LadyFinders", "CODEX5FTW", "actionpapa", "DendiXZ", "Kakukaki",
    "Papipapooo", "XrayBoi", "StresssLife", "Xress", "SirSnowman",
    "Youngomw", "MiloIce", "GLHF", "HAHAHEHA", "7Knight", "hokkaido",
    "holangpu", "Mooogi", "Pookie", "iguy", "mrDEADMAN", "Nettto",
    "AK47HAX", "Deklass", "Yoonz", "XuFeng", "Samsara", "LachBata",
    "FenTen", "Sukunaa", "Roachy", "Mwhit", "Sakanya", "Farox",
    "jeyo", "dLLM", "izzyLike", "Greul", "Rejca", "thanh", "Brutezzi",
    "SASORI77", "MangoDigger", "jbnz", "2pacHero", "BabyEIEI", "someyell",
    "Rafeal", "tpolben", "bohaco", "Psychos", "Phrost", "Boxxerz", "Mirwen",
    "gonetaro", "yumenko", "RyveN", "DelHeinze", "noakie", "Akin", "Beekay",
    "Resh42", "sucht", "RastaMAN", "LeonKing17", "VerCos360", "Piggy", "Flame1998",
    "RUNBOI", "turtle001", "LAPIN", "MaddoxBaby", "VGD", "BuiKing",
    "NightKidz", "Kangcez"
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
    "Oliver", "Ryan", "Samuel", "Steven",
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
    WORDS_PLAYER_USERNAME +
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

    WORD_INDEX += random.randint(1,3)

    parts.append(base)

    if WORD_POOL:
        body = str(WORD_POOL[WORD_INDEX % len(WORD_POOL)])
    else:
        body = "body"
        
    WORD_INDEX += random.randint(1,3)
    
    parts.append(body)

    if postfix:
        parts.append(postfix)

    if random.random() < 0.1:
        username = "_".join(parts)
    else:
        username = "".join(parts)

    if random.random() < 0.25:
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
