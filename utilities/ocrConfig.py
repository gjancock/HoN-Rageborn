import pytesseract
import sys
import os
from utilities.common import resource_path

def ensure_tesseract_configured():
    """
    Configure pytesseract correctly for:
    - PyInstaller exe  → bundled tesseract + tessdata
    - Dev mode         → system tesseract + system tessdata
    """

    if hasattr(sys, "_MEIPASS"):
        # Packaged mode
        pytesseract.pytesseract.tesseract_cmd = resource_path(
            "tesseract/tesseract.exe"
        )
        os.environ["TESSDATA_PREFIX"] = resource_path(
            "tesseract/tessdata"
        )
    else:
        if "TESSDATA_PREFIX" in os.environ:
            del os.environ["TESSDATA_PREFIX"]

def get_config():

     # DEV MODE: absolutely NO tessdata override
    if not hasattr(sys, "_MEIPASS"):
        return (
            r"--oem 3 --psm 7 "
            r"-c tessedit_char_whitelist="
            r"abcdefghijklmnopqrstuvwxyz"
            r"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            r"0123456789_-"
        )

    # PACKAGED MODE ONLY
    return (
        rf'--tessdata-dir "{resource_path("tesseract/tessdata")}" '
        r"--oem 3 --psm 7 "
        r"-c tessedit_char_whitelist="
        r"abcdefghijklmnopqrstuvwxyz"
        r"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        r"0123456789_-"
    )
