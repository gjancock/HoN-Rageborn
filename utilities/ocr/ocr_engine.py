import cv2
import utilities.constants as constant

from utilities.ocr.tesseract_engine import tesseract_read_debug
from utilities.ocr.preprocess import preprocess_for_ocr

from utilities.paths import get_user_data_dir
from pathlib import Path
from utilities.loggerSetup import setup_ocr_logger

logger = setup_ocr_logger()

# ============================================================
# CONFIG
# ============================================================

ROW_HEIGHT = 16      # tuned by you
TOP_OFFSET = 0
DEBUG_DIR = get_user_data_dir() / "ocr_debug" / "rows"

# ============================================================
# HELPERS
# ============================================================

def normalize_username(text: str) -> str:
    if not text:
        return ""

    text = text.strip()
    text = text.strip("_-,")

    return text


def fix_common_ocr_errors(text: str) -> str:
    """
    Fix very common OCR mistakes without guessing too much.
    """
    if text.endswith("l"):
        return text[:-1] + "1"
    if text.endswith("I"):
        return text[:-1] + "1"
    return text


def split_into_rows(team, image, offset_x: int = 0):
    h, w = image.shape[:2]
    rows = []

    team_dir = DEBUG_DIR / team
    team_dir.mkdir(parents=True, exist_ok=True)

    y = TOP_OFFSET
    index = 0

    if offset_x < 0:
        x1 = 0
        x2 = w + offset_x
    else:
        x1 = offset_x
        x2 = w

    x1 = max(0, x1)
    x2 = min(w, x2)

    while y < h:
        row = image[y : min(y + ROW_HEIGHT, h), x1:x2]

        # ignore tiny scraps
        if row.shape[0] < ROW_HEIGHT * 0.6:
            break

        rows.append((index, row))

        cv2.imwrite(
            str(team_dir / f"row_{index}.png"),
            row
        )

        index += 1
        y += ROW_HEIGHT

    logger.warning(f"[OCR] Saved {index} row images to {team_dir}")
    return rows


def ocr_single_row(row_img, index):
    """
    OCR a single row and return everything found.
    """
    processed = preprocess_for_ocr(row_img)

    items = tesseract_read_debug(processed, psm=7)
    if not items:
        return {
            "row": index,
            "raw": "",
            "text": "",
            "confidence": 0.0
        }

    items = sorted(items, key=lambda i: i["x"])

    raw_text = "".join(i["text"] for i in items)
    avg_conf = sum(i["confidence"] for i in items) / len(items)

    text = normalize_username(raw_text)
    text = fix_common_ocr_errors(text)

    logger.warning(
        f"[OCR-ROW {index}] raw='{raw_text}' norm='{text}' conf={avg_conf:.1f}"
    )

    return {
        "row": index,
        "raw": raw_text,
        "text": text,
        "confidence": avg_conf
    }

# ============================================================
# PUBLIC API
# ============================================================

def read_usernames_from_region(name_region, team):
    """
    OCR the name list region and return ALL rows found.
    Nothing is filtered out.
    """    

    if name_region is None:
        return []
    
    TEAM_ROW_OFFSET_X = {
        constant.TEAM_LEGION: -25,
        constant.TEAM_HELLBOURNE: -20,
    }

    offset_x = TEAM_ROW_OFFSET_X.get(team, 0)

    rows = split_into_rows(team, name_region, offset_x=offset_x)

    results = []

    for index, row in rows:
        result = ocr_single_row(row, index)
        results.append(result)

    return results
