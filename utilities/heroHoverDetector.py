from PIL import ImageGrab, ImageOps
import pytesseract
from utilities.ocrConfig import OCR_CONFIG

def detect_hero_hover_text(region):
    """
    region = dict with keys: x, y, w, h
    Returns:
        - None        → no hover info
        - string text → hover info detected
    """

    x = region["x"]
    y = region["y"]
    w = region["w"]
    h = region["h"]

    # 1️⃣ Capture region
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))

    # 2️⃣ Preprocess (important for tiny text)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)

    # Optional: threshold for very small fonts
    img = img.point(lambda p: 255 if p > 160 else 0)

    # 3️⃣ OCR
    text = pytesseract.image_to_string(
        img,
        config=OCR_CONFIG
    )

    # 4️⃣ Clean result
    text = text.strip()

    if not text:
        return None

    return text
