from pynput import mouse
import pyautogui
from datetime import datetime

OUTPUT_FILE = "mouse_coordinates.txt"

def on_click(x, y, button, pressed):
    if pressed:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} | x={x}, y={y}\n"

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(line)

        print(f"[RECORDED] {line.strip()}")

def main():
    print("===================================")
    print(" Mouse Coordinate Recorder Started ")
    print(" Click anywhere to record position ")
    print(" Press CTRL+C to stop")
    print("===================================")

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

if __name__ == "__main__":
    main()
