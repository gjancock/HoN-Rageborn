import pytesseract

# Explicit path (important for PyInstaller)
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

OCR_CONFIG = (
    r"--oem 3 --psm 7 "
    r"-c tessedit_char_whitelist="
    r"abcdefghijklmnopqrstuvwxyz"
    r"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    r"0123456789"
)
