# utilities/chatUtilities.py
import os
import sys
from utilities.common import resource_path
from itertools import cycle
import core.state as state
import utilities.constants as constant
from utilities.paths import get_user_data_dir

MAX_CHAT_LENGTH = 150

_chat_iterators = {}

# Wrapper function
def get_picking_chats():
    return read_chat_file(get_chat_path("chat_picking.txt"))

def get_next_picking_chat():
    return get_next_chat_line(get_chat_path("chat_picking.txt"))

def get_ingame_chats():
    return read_chat_file(get_chat_path("chat_ingame.txt"))

def get_next_ingame_chat():
    return get_next_chat_line(get_chat_path("chat_ingame.txt"))

#
def build_chat_context():
    team = state.INGAME_STATE.getCurrentTeam()
    map = state.INGAME_STATE.getCurrentMap()
    focRole = state.INGAME_STATE.getFocRole()

    MAP_NAMES = {
        constant.MAP_FOC: "Forest of Caldavar",
        constant.MAP_MIDWAR: "Midwars",
    }

    MAP_SHORT = {
        constant.MAP_FOC: "FoC",
        constant.MAP_MIDWAR: "MW",
    }

    return {
        "team": team,
        "opponent_team": constant.TEAM_LEGION if team == constant.TEAM_HELLBOURNE else constant.TEAM_HELLBOURNE,
        "map": MAP_NAMES.get(map, "Unknown Map"),
        "map_shortform": MAP_SHORT.get(map, "N/A"),
        "foc_role": focRole
    }


def apply_chat_placeholders(text: str) -> str:
    """
    Replace predefined chat placeholders with actual values.

    Example:
    {%team%} -> Legion
    {%map%} -> Forest of Caldavar
    """
    context = build_chat_context()

    if not text or not context:
        return text

    for key, value in context.items():
        placeholder = f"{{%{key}%}}"
        text = text.replace(placeholder, str(value))

    return text


def get_next_chat_line(path):
    """
    Returns the next chat line in order (loops automatically).
    """
    if path not in _chat_iterators:
        lines = read_chat_file(path)
        if not lines:
            return None
        _chat_iterators[path] = cycle(lines)

    return next(_chat_iterators[path])

def get_chat_path(filename: str) -> str:
    return str(get_user_data_dir() / filename)

def read_chat_file(path: str, default_relative_path: str | None = None) -> list[str]:
    """
    Read chat file into a list of strings.

    If file does not exist:
    - copy from bundled default (if provided)
    - otherwise return empty list
    """
    if not os.path.exists(path):
        if default_relative_path:
            try:
                default_path = resource_path(default_relative_path)
                if os.path.exists(default_path):
                    with open(default_path, "r", encoding="utf-8") as src:
                        content = src.read()

                    with open(path, "w", encoding="utf-8") as dst:
                        dst.write(content)
            except Exception:
                return []

        else:
            return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return [
                line.rstrip("\n")
                for line in f
                if line.strip()
            ]
    except Exception:
        return []



def validate_chat_lines(lines: list[str]) -> list[str]:
    """
    Enforce 150-char limit and strip whitespace.
    """
    validated = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        validated.append(line[:MAX_CHAT_LENGTH])
    return validated


def save_chat_file(path: str, lines: list[str]) -> None:
    """
    Save validated lines to disk.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
