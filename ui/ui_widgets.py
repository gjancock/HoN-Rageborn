# ui/ui_widgets.py
import tkinter as tk


def labeled_entry(parent, label, default=""):
    tk.Label(parent, text=label, anchor="w").pack(fill="x")
    e = tk.Entry(parent)
    e.pack(fill="x", pady=2)
    if default:
        e.insert(0, default)
    return e


def set_endless_mode_ui_running(button):
    button.config(
        text="Hit F11 to stop",
        fg="red",
        state="disabled"
    )


def set_endless_mode_ui_idle(button):
    button.config(
        text="Start Endless Mode",
        fg="black",
        state="normal"
    )
