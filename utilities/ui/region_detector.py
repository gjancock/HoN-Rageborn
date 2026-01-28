import cv2
from typing import Optional, Tuple

from utilities.paths import get_launcher_dir

# ============================================================
# CONSTANTS & CONFIG
# ============================================================

ANCHOR_MATCH_THRESHOLD = 0.75

TEAM_UI_CONFIG = {
    "legion": {
        "anchor_image": "legion.png",
        "crop": {
            "offset_x": -25,
            "offset_y_from_anchor": 0,
            "width": 320,
            "height": 220,
        },
    },
    "hellbourne": {
        "anchor_image": "hellbourne.png",
        "crop": {
            "offset_x": -20,
            "offset_y_from_anchor": 0,
            "width": 320,
            "height": 220,
        },
    },
}

ANCHOR_DIR = get_launcher_dir() / "assets" / "anchors"

AnchorRect = Tuple[int, int, int, int]  # x, y, w, h

# ============================================================
# INTERNAL HELPERS
# ============================================================

def _load_anchor_image(filename: str):
    path = ANCHOR_DIR / filename
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Failed to load anchor image: {path}")
    return img


def _find_anchor(
    screenshot,
    anchor_image
) -> Optional[AnchorRect]:
    """
    Generic template matcher.
    """

    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(
        gray,
        anchor_image,
        cv2.TM_CCOEFF_NORMED
    )

    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < ANCHOR_MATCH_THRESHOLD:
        return None

    x, y = max_loc
    h, w = anchor_image.shape

    return (x, y, w, h)

# ============================================================
# PUBLIC API — ANCHORS
# ============================================================

def find_team_anchor(screenshot, team: str) -> Optional[AnchorRect]:
    """
    Find the anchor (team header) for the given team.
    """

    if team not in TEAM_UI_CONFIG:
        raise ValueError(f"Unknown team: {team}")

    anchor_filename = TEAM_UI_CONFIG[team]["anchor_image"]
    anchor_image = _load_anchor_image(anchor_filename)

    return _find_anchor(screenshot, anchor_image)

# ============================================================
# PUBLIC API — REGION CROP
# ============================================================

def crop_name_list_region(screenshot, anchor_rect: AnchorRect, team: str):
    """
    Crop the player name list region for a given team.
    """

    if team not in TEAM_UI_CONFIG:
        raise ValueError(f"Unknown team: {team}")

    crop_cfg = TEAM_UI_CONFIG[team]["crop"]

    x, y, w, h = anchor_rect

    x1 = max(0, x + crop_cfg["offset_x"])
    y1 = max(0, y + h + crop_cfg["offset_y_from_anchor"])

    x2 = min(screenshot.shape[1], x1 + crop_cfg["width"])
    y2 = min(screenshot.shape[0], y1 + crop_cfg["height"])

    return screenshot[y1:y2, x1:x2]
