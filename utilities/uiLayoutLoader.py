import json

def load_ui_layout():
    with open("datasets/coordinates_1920x1080.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_player_rows(ui_layout, team):
    return [
        (
            row["region"]["x"],
            row["region"]["y"],
            row["region"]["w"],
            row["region"]["h"],
            row["index"]
        )
        for row in ui_layout["picking_phase"][team]["player_rows"]
    ]

def get_hero_hover_region(ui_layout):
    return ui_layout["picking_phase"]["hero_hover_information"]

