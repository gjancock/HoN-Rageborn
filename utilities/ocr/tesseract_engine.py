import pytesseract
import logging
import cv2
import os

from pytesseract import Output
from pathlib import Path
from utilities.paths import TESSERACT_EXE, TESSDATA_DIR, get_user_data_dir

logger = logging.getLogger("OCR_DEBUG")

DEBUG_DIR = get_user_data_dir() / "ocr_debug"


def is_tesseract_available():
    logger.warning(f"[OCR_DEBUG] Checking tesseract at: {TESSERACT_EXE}")
    return TESSERACT_EXE.exists()


def tesseract_read_text(image, *, whitelist=None, numeric=False, psm=11):
    logger.warning("[OCR_DEBUG] tesseract_read_text() CALLED")

    if not TESSERACT_EXE.exists():
        logger.error("[OCR_DEBUG] tesseract.exe NOT FOUND")
        return ""

    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

    DEBUG_DIR.mkdir(exist_ok=True)

    cv2.imwrite(
        str(DEBUG_DIR / "ocr_input_to_tesseract.png"),
        image
    )
    logger.warning("[OCR_DEBUG] Saved ocr_input_to_tesseract.png")

    config = f"--psm {psm}"

    if numeric:
        config += " -c tessedit_char_whitelist=0123456789"
    elif whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"

    try:
        text = pytesseract.image_to_string(image, config=config)
        return text.strip()
    except Exception:
        logger.exception("[OCR_DEBUG] Tesseract OCR failed")
        return ""


def tesseract_read_debug(image, *, psm=7):
    if not TESSERACT_EXE.exists():
        logger.error("[OCR_DEBUG] tesseract.exe NOT FOUND")
        return []

    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

    config = f"--psm {psm}"

    data = pytesseract.image_to_data(
        image,
        config=config,
        output_type=Output.DICT
    )

    results = []

    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])

        if text and conf > 0:
            results.append({
                "text": text,
                "confidence": conf,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
            })

    return results
