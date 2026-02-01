import random

# ==================================================
# WORD POOLS
# ==================================================

FIRST_NAMES_MALE = [
    "Adam", "Alex", "Aaron", "Ben", "Brian",
    "Chris", "Daniel", "David", "Eric", "Ethan",
    "Jack", "James", "Jason", "John", "Kevin",
    "Lucas", "Mark", "Michael", "Nathan",
    "Oliver", "Ryan", "Samuel", "Steven",
    "Thomas", "William"
]

FIRST_NAMES_FEMALE = [
    "Alice", "Amy", "Anna", "Ashley", "Catherine",
    "Emily", "Emma", "Grace", "Hannah", "Jessica",
    "Julia", "Laura", "Linda", "Lucy", "Michelle",
    "Natalie", "Rachel", "Sarah", "Sophia"
]

FIRST_NAMES_UNISEX = [
    "Alex", "Jordan", "Taylor", "Morgan",
    "Casey", "Jamie", "Avery", "Riley"
]

LAST_NAMES_COMMON = [
    "Brown", "Clark", "Davis", "Evans", "Garcia",
    "Harris", "Johnson", "Jones", "Lee", "Lewis",
    "Martin", "Miller", "Moore", "Roberts",
    "Smith", "Taylor", "Walker", "White", "Wilson"
]

LAST_NAMES_ASIAN = [
    "Lim", "Tan", "Wong", "Lee", "Ong",
    "Teoh", "Khaw", "Chu", "Loo"
]

# ==================================================
# FIRST NAME GENERATOR
# ==================================================

def generate_firstname(gender: str | None = None) -> str:
    """
    Generate a realistic human first name.

    gender:
        - "male"
        - "female"
        - None (mixed pool)
    """

    if gender == "male":
        pool = FIRST_NAMES_MALE + FIRST_NAMES_UNISEX
    elif gender == "female":
        pool = FIRST_NAMES_FEMALE + FIRST_NAMES_UNISEX
    else:
        pool = (
            FIRST_NAMES_MALE +
            FIRST_NAMES_FEMALE +
            FIRST_NAMES_UNISEX
        )

    return random.choice(pool)


# ==================================================
# LAST NAME GENERATOR
# ==================================================

def generate_lastname(region: str | None = None) -> str:
    """
    Generate a realistic human last name.

    region:
        - "western"
        - "asian"
        - None (mixed pool)
    """

    if region == "western":
        pool = LAST_NAMES_COMMON
    elif region == "asian":
        pool = LAST_NAMES_ASIAN
    else:
        pool = LAST_NAMES_COMMON + LAST_NAMES_ASIAN

    return random.choice(pool)
