# Refer to coordinates_resolutionsize.json
import utilities.constants as constant
import random

_coords = None

def init(coords):
    global _coords
    _coords = coords

#
def get_matchmaking_tuner_coord(type="fastest"):
    allowed = {"fastest", "balanced", "fairness"}

    if type not in allowed:
        raise ValueError(f"Invalid matchmaking tuner type: {type}")

    try:
        node = _coords["matchmaking_panel"]["matchmaking_tuner"][type]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: matchmaking_panel.matchmaking_tuner.{type}"
        ) from e
    
#
def get_queue_button_coord():
    try:
        node = _coords["matchmaking_panel"]["enter_queue_button"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: matchmaking_panel.enter_queue_button"
        ) from e
    
#
def get_picking_dismiss_safezone_coord():
    try:
        node = _coords["picking_phase"]["dismiss_safezone"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: picking_phase.dismiss_safezone"
        ) from e
    
#
def get_friendly_tower_coord(map, team, lane, number):
    map_allowed = {constant.MAP_FOC, constant.MAP_MIDWAR}

    if map not in map_allowed:
        raise ValueError(f"Invalid map type: {map}")
    
    team_allowed = {constant.TEAM_LEGION, constant.TEAM_HELLBOURNE}

    if team not in team_allowed:
        raise ValueError(f"Invalid team type: {team}")
    
    if map == constant.MAP_FOC:
        lane_allowed = {constant.LANE_TOP, constant.LANE_MID, constant.LANE_BOT}
        number_allowed = {1, 2, 3}

    elif map == constant.MAP_MIDWAR:
        lane_allowed = {constant.LANE_MID}
        number_allowed = {1, 2}

    else:
        raise ValueError(f"Invalid map type: {map}")

    if lane not in lane_allowed:
        raise ValueError(f"Invalid lane type '{lane}' for map '{map}'")

    if number not in number_allowed:
        raise ValueError(f"Invalid number '{number}' for map '{map}'")

    try:
        node = _coords["in_game"][map][team][f"friendly_{lane}"][f"tower_{number}"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: in_game.{map}.{team}.friendly_{lane}.tower_{number}"
        ) from e
    
#
def get_enemy_tower_coord(map, team, lane, number):
    map_allowed = {constant.MAP_FOC, constant.MAP_MIDWAR}

    if map not in map_allowed:
        raise ValueError(f"Invalid map type: {map}")
    
    team_allowed = {constant.TEAM_LEGION, constant.TEAM_HELLBOURNE}

    if team not in team_allowed:
        raise ValueError(f"Invalid team type: {team}")
    
    if map == constant.MAP_FOC:
        lane_allowed = {constant.LANE_TOP, constant.LANE_MID, constant.LANE_BOT}
        number_allowed = {1, 2, 3}

    elif map == constant.MAP_MIDWAR:
        lane_allowed = {constant.LANE_MID}
        number_allowed = {1, 2}

    else:
        raise ValueError(f"Invalid map type: {map}")

    if lane not in lane_allowed:
        raise ValueError(f"Invalid lane type '{lane}' for map '{map}'")

    if number not in number_allowed:
        raise ValueError(f"Invalid number '{number}' for map '{map}'")

    try:
        node = _coords["in_game"][map][team][f"enemy_{lane}"][f"tower_{number}"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: in_game.{map}.{team}.enemy_{lane}.tower_{number}"
        ) from e
    
#
def get_friendly_base_coord(map, team):
    map_allowed = {constant.MAP_FOC, constant.MAP_MIDWAR}

    if map not in map_allowed:
        raise ValueError(f"Invalid map type: {map}")
    
    team_allowed = {constant.TEAM_LEGION, constant.TEAM_HELLBOURNE}

    if team not in team_allowed:
        raise ValueError(f"Invalid team type: {team}")
    
    try:
        node = _coords["in_game"][map][team]["friendly_base"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: in_game.{map}.{team}.friendly_base"
        ) from e
    
#
def get_enemy_base_coord(map, team):
    map_allowed = {constant.MAP_FOC, constant.MAP_MIDWAR}

    if map not in map_allowed:
        raise ValueError(f"Invalid map type: {map}")
    
    team_allowed = {constant.TEAM_LEGION, constant.TEAM_HELLBOURNE}

    if team not in team_allowed:
        raise ValueError(f"Invalid team type: {team}")
    
    try:
        node = _coords["in_game"][map][team]["enemy_base"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing coord: in_game.{map}.{team}.enemy_base"
        ) from e
    
#
def get_in_game_shop_initiation_category_coord():
    try:
        node = _coords["in_game"]["shop"]["initiation"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.initiation"
        ) from e
    
def get_in_game_shop_consumables_category_coord():
    try:
        node = _coords["in_game"]["shop"]["consumables"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.consumables"
        ) from e
    
def get_in_game_shop_boots_category_coord():
    try:
        node = _coords["in_game"]["shop"]["boots"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.boots"
        ) from e
    
def get_in_game_shop_damage_category_coord():
    try:
        node = _coords["in_game"]["shop"]["damage"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.damage"
        ) from e
    
def get_in_game_shop_defense_category_coord():
    try:
        node = _coords["in_game"]["shop"]["defense"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.defense"
        ) from e
    
def get_in_game_shop_supportive_category_coord():
    try:
        node = _coords["in_game"]["shop"]["supportive"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.supportive"
        ) from e
    
def get_in_game_shop_enchantment_category_coord():
    try:
        node = _coords["in_game"]["shop"]["enchantment"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.shop.enchantment"
        ) from e
    
def get_heroes_coord(hero):
    try:
        hero = hero.lower()

        if hero in _coords["picking_phase"]["heroes"]:
            node = _coords["picking_phase"]["heroes"][hero]
            return node["x"], node["y"]
        else:
            return False

    except KeyError as e:
        raise ValueError(
            f"Missing item: picking_phase.heroes.{hero}"
        ) from e
    
def get_role_heroes_coord(role):
    try:
        role_allowed = {constant.FOC_ROLE_CARRY, 
                        constant.FOC_ROLE_HARD_SUPPORT, 
                        constant.FOC_ROLE_MID, 
                        constant.FOC_ROLE_OFFLANE, 
                        constant.FOC_ROLE_SOFT_SUPPORT, 
                        constant.FOC_ROLE_JUNGLE,
                        constant.FOC_ROLE_SOLO_OFFLANE
                        }

        if role not in role_allowed:
            raise ValueError(f"Invalid role type: {role}")
        
        roles = _coords["picking_phase"]["role"]
        
        hero = random.choice(list(roles[role].keys()))

        node = roles[role][hero]
        return hero, node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: picking_phase.role.{role}.{hero}"
        ) from e
    
def get_hero_top_portrait_coord(map, team, pos):
    try:
        map_allowed = {constant.MAP_FOC, constant.MAP_MIDWAR}
        if map not in map_allowed:
            raise ValueError(f"Invalid map type: {map}")
        
        team_allowed = {constant.TEAM_HELLBOURNE, constant.TEAM_LEGION}
        if team not in team_allowed:
            raise ValueError(f"Invalid team type: {team}")
        
        if pos not in range(1, 6):
            raise ValueError(f"Invalid pos number: {pos}")
        
        node = _coords["in_game"][map][team][f"hero_portrait_{pos}"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.{map}.{team}.hero_portrait_{pos}"
        ) from e
    
def get_in_game_center_hero_coord():
    try:
        node = _coords["in_game"]["center_hero"]
        return node["x"], node["y"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: in_game.center_hero"
        ) from e
    
# String
def get_foc_role_information(role):
    try:
        role_allowed = {constant.FOC_ROLE_CARRY, constant.FOC_ROLE_HARD_SUPPORT, constant.FOC_ROLE_MID, constant.FOC_ROLE_OFFLANE, constant.FOC_ROLE_SOFT_SUPPORT}

        if role not in role_allowed:
            raise ValueError(f"Invalid role type: {role}")
        
        return _coords["picking_phase"]["role_information"][role]
    except KeyError as e:
        raise ValueError(
            f"Missing item: picking_phase.role_information.{role}"
        ) from e

def get_app_icon():
    try:
        return _coords["meta"]["app_icon"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: meta.app_icon"
        ) from e
    
def get_app_icon_default():
    try:
        return _coords["meta"]["app_icon_default"]
    except KeyError as e:
        raise ValueError(
            f"Missing item: meta.app_icon_default"
        ) from e