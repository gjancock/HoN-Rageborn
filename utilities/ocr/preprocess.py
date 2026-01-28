import cv2

def preprocess_for_ocr(img):
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Heavy upscale for small UI fonts
    gray = cv2.resize(
        gray,
        None,
        fx=3.0,
        fy=3.0,
        interpolation=cv2.INTER_CUBIC
    )

    # Mild blur to connect strokes
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # OTSU threshold (NO adaptive)
    _, thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return thresh
