import win32gui
import win32con
import win32api


def is_fullscreen(hwnd):
    win_left, win_top, win_right, win_bottom = win32gui.GetWindowRect(hwnd)
    win_width = win_right - win_left
    win_height = win_bottom - win_top

    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)

    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

    has_border = style & win32con.WS_BORDER
    has_caption = style & win32con.WS_CAPTION

    fullscreen = (
        win_left <= 0
        and win_top <= 0
        and win_width >= screen_width
        and win_height >= screen_height
        and not has_border
        and not has_caption
    )

    return fullscreen