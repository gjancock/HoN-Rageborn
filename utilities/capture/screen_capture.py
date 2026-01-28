import cv2
import numpy as np
import mss


def capture_fullscreen():
    """
    Capture the entire primary monitor and return a BGR OpenCV image.
    """

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 1 = primary monitor
        img = np.array(sct.grab(monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img
