# ui/chat_editor.py
import tkinter as tk
import utilities.constants as constant

from utilities.chatUtilities import (
    read_chat_file,
    validate_chat_lines,
    save_chat_file,
)

def force_newline_at_end(event, text_widget):
    text_widget.insert("end", "\n")
    text_widget.see("end")
    return "break"


def enforce_line_length(event, text_widget):
    index = text_widget.index("insert")
    line, col = map(int, index.split("."))

    start = f"{line}.0"
    end = f"{line}.end"

    line_text = text_widget.get(start, end)

    if len(line_text) > constant.MAX_CHAT_LEN:
        text_widget.delete(f"{line}.{constant.MAX_CHAT_LEN}", end)
        return "break"
    

def build_chat_editor(parent, title, path, default_relative_path):
    frame = tk.LabelFrame(parent, text=title, padx=8, pady=6)
    frame.pack(fill="both", expand=True, padx=10, pady=6)

    scrollbar = tk.Scrollbar(frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    text = tk.Text(
        frame,
        height=8,
        wrap="word",
        undo=True,
        font=("Consolas", 10),
        spacing1=4,
        spacing3=4,
        yscrollcommand=scrollbar.set
    )
    text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text.yview)

    lines = read_chat_file(path, default_relative_path)
    text.insert("1.0", "\n".join(lines))
    highlight_lines(text)

    # 🔒 Enforcements
    text.bind("<Key>", lambda e: enforce_line_length(e, text))
    text.bind("<Return>", lambda e: force_newline_at_end(e, text))

    # 🔁 Highlight only on logical modification
    text.bind(
        "<<Modified>>",
        lambda e: (
            text.edit_modified(False),
            highlight_lines(text)
        )
    )

    return text


def save_chat_settings(
    *,
    picking_text,
    ingame_text,
    picking_path,
    ingame_path,
):
    picking_lines = picking_text.get("1.0", "end").splitlines()
    ingame_lines = ingame_text.get("1.0", "end").splitlines()

    picking_lines = validate_chat_lines(picking_lines)
    ingame_lines = validate_chat_lines(ingame_lines)

    save_chat_file(picking_path, picking_lines)
    save_chat_file(ingame_path, ingame_lines)


def highlight_lines(text_widget):
    text_widget.tag_configure("even", background="#f7f7f7")
    text_widget.tag_configure("odd", background="#ffffff")

    text_widget.tag_remove("even", "1.0", "end")
    text_widget.tag_remove("odd", "1.0", "end")

    end_line = int(text_widget.index("end-1c").split(".")[0])

    for i in range(1, end_line + 1):
        tag = "even" if i % 2 == 0 else "odd"
        text_widget.tag_add(tag, f"{i}.0", f"{i}.end")


def reset_chat_to_default(text_widget, target_path, default_relative_path):
    lines = read_chat_file(target_path, default_relative_path)

    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", "\n".join(lines))
    highlight_lines(text_widget)


def build_chat_placeholder_guide(parent):
    frame = tk.LabelFrame(
        parent,
        text="Dynamic Parameters",
        padx=8,
        pady=6
    )
    frame.pack(fill="x", padx=10, pady=(6, 10))

    guide_text = (
        "Available keys:\n"
        "  team / opponent_team / map / map_shortform / foc_role\n\n"
        "Usage example:\n"
        "  I'm in {%team%} team.\n"
        "Output:\n"
        "  I'm in Legion team."
    )

    label = tk.Label(
        frame,
        text=guide_text,
        justify="left",
        anchor="w",
        font=("Consolas", 9),
        fg="#CE3030"
    )
    label.pack(fill="x")