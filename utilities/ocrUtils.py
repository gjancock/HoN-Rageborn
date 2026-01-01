from PIL import ImageGrab, ImageOps
import pytesseract
from utilities.ocrConfig import get_config

def ocr_region(x, y, w, h):
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))

    # Optional but recommended preprocessing
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)

    text = pytesseract.image_to_string(
        img,
        config=get_config()
    )

    return text.strip()
