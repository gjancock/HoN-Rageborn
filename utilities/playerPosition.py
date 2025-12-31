from utilities.uiLayoutLoader import get_player_rows
from utilities.ocrUtils import ocr_region
import utilities.constants as constant

def detect_team_and_position(username, ui_layout):
    username = username.lower()

    # 1️⃣ Check Legion first
    for x, y, w, h, index in get_player_rows(ui_layout, constant.TEAM_LEGION):
        text = ocr_region(x, y, w, h).lower()
        if username in text:
            return constant.TEAM_LEGION, index

    # 2️⃣ If not found, check Hellbourne
    for x, y, w, h, index in get_player_rows(ui_layout, constant.TEAM_HELLBOURNE):
        text = ocr_region(x, y, w, h).lower()
        if username in text:
            return constant.TEAM_HELLBOURNE, index

    return None, None