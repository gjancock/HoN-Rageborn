import pytesseract
import os
from utilities.common import resource_path

def ensure_tesseract_configured():
    """
    Ensure pytesseract is correctly configured.
    Safe to call multiple times.
    """
    if pytesseract.pytesseract.tesseract_cmd != "tesseract":
        return

    pytesseract.pytesseract.tesseract_cmd = resource_path(
        "tesseract/tesseract.exe"
    )

    # IMPORTANT: must point to tessdata directory
    os.environ["TESSDATA_PREFIX"] = resource_path(
        "tesseract/tessdata"
    )


OCR_CONFIG = (
    r"--oem 3 --psm 7 "
    rf'--tessdata-dir "{resource_path("tesseract/tessdata")}" '
    r"-c tessedit_char_whitelist="
    r"abcdefghijklmnopqrstuvwxyz"
    r"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    r"0123456789"
    r"_-"
)