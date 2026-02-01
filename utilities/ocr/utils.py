import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image

# Optional: set this once globally if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def ocr_read_single_line_region(
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    threshold: bool = True,
    invert: bool = False,
    whitelist: str | None = None,
    debug: bool = False,
) -> str:
    """
    OCR a SINGLE LINE of text from a fixed screen region.

    Args:
        x, y, w, h : screen coordinates
        threshold : apply binary threshold (recommended)
        invert    : invert colors (useful for light text on dark bg)
        whitelist : limit OCR characters (e.g. '0123456789%')
        debug     : show the processed image window

    Returns:
        Cleaned OCR string (single line)
    """

    # 1️⃣ Screenshot region
    screenshot = pyautogui.screenshot(region=(x, y, w, h))
    img = np.array(screenshot)

    # 2️⃣ Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3️⃣ Optional invert
    if invert:
        gray = cv2.bitwise_not(gray)

    # 4️⃣ Optional threshold (huge OCR improvement)
    if threshold:
        gray = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

    # 5️⃣ OCR config (SINGLE LINE)
    config = "--psm 7"  # single text line
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"

    text = pytesseract.image_to_string(gray, config=config)

    # 6️⃣ Cleanup
    text = text.strip()
    text = " ".join(text.split())  # collapse weird spacing

    if debug:
        cv2.imshow("OCR Debug", gray)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return text
