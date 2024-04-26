import time
import json
import copy
from pathlib import Path
from constants import *
from copy import deepcopy
from constants import *
from enums.direction import Direction
from helper import *


def get_geometry(obj):
    obj_copy = deepcopy(obj)
    return {
        "position": obj_copy["position"],
        "height": obj_copy["height"],
        "width": obj_copy["width"]
    }


def recv_socket_data(sock):
    BUFF_SIZE = 4096  # 4 KiB
    data = b''
    while True:
        time.sleep(0.00001)
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break

    return data

def manhattan_distance(pos1, pos2):
    # Calculate the Manhattan distance from pos1 to pos2
    return abs(pos2[0] - pos1[0]) + abs(pos2[1] - pos2[1])

def euclidean_distance(pos1, pos2):
    # Calculate Euclidean distance between two points
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5

def calculate_crowdedness_factor(player:dict, box:dict, observation:dict) -> float:
    """Given an observation, a player, and a box region, calculate how crowded that region is

    Args:
        player (dict): the agent excluded in the calculation
        box (dict): the region of interest {"westmost":float, "southmost":float, "eastmost":float, "northmost":float}
        observation (dict): observation containing the players in the map
    Returns:
        how much empty space per unit area
    """
    area = abs(box['westmost'] - box['eastmost']) * abs(box['northmost'] - box['southmost'])
    occupied_area = 0
    for p in observation['players']:
        if p['index'] == player['index']: # don't count our player
            continue
        if obj_overlap_with_box(p, box):
            occupied_area += p['width']*p['height']
    for c in observation['carts']:
        if c['owner'] == player['index']: # don't count our cart
            continue
        if obj_overlap_with_box(c, box):
            occupied_area += c['width'] * c['height']
    for b in observation['baskets']:
        if b['owner'] == player['index']: # don't count our basket
            continue
        if obj_overlap_with_box(b, box):
            occupied_area += b['width'] * b['height']
    return 1.0 - (occupied_area / area)
    
    # divide number of players by area of the box region
    return player_count / (abs(box['westmost'] - box['eastmost']) * abs(box['northmost'] - box['southmost']))

def bounding_box(place:dict) -> dict:
    """find the bounding box for a place.

    Args:
        place (dict): a dictionary containing height, width and position of the object

    Returns:
        dict: a dictionary containing the northmost y, the southmost y, and westmost x and the eastmost x
    """
    upper_left = place['position']
    height = place['height']
    width = place['width']
    return {"northmost":upper_left[1], "westmost":upper_left[0], "southmost":upper_left[1]+height, "eastmost":upper_left[0]+width}

def find_midpoint(interact_box:dict) -> tuple[float, float]:
    """find the midpoint along an edge of an interact box. Which edge it is depends on the direction the player needs to face in the box

    Args:
        interact_box (dict): an interact box for an object

    Returns:
        tuple[float, float]: (x, y)
    """
    player_needs_to_face = interact_box['player_needs_to_face']
    if player_needs_to_face == Direction.NORTH.name:#this box is to the SOUTH of the interaction object
        edge_y = interact_box['southmost']
        edge_x = (interact_box['eastmost'] - interact_box['westmost']) / 2.0 + interact_box['westmost']
        return (edge_x, edge_y)
    elif player_needs_to_face == Direction.SOUTH.name:#this box is to the NORTH of the interaction object
        edge_y = interact_box['northmost']
        edge_x = (interact_box['eastmost'] - interact_box['westmost']) / 2.0 + interact_box['westmost']
        return (edge_x, edge_y)
    elif player_needs_to_face == Direction.WEST.name:#this box is to the EAST of the interaction object
        edge_x = interact_box['eastmost']
        edge_y = (interact_box['southmost'] - interact_box['northmost']) / 2.0 + interact_box['northmost']
        return (edge_x, edge_y)
    else:#this box is to the WEST of the interaction object
        edge_x = interact_box['westmost']
        edge_y = (interact_box['southmost'] - interact_box['northmost']) / 2.0 + interact_box['northmost']
        return (edge_x, edge_y)

def player_interact_area(player) -> list:
    interact_boxes = four_side_interact_area(player)
    dir = player['direction']
    player['interact_box'] = interact_boxes[dir]
    return player['interact_box']

def one_side_interact_area(place_obj) -> list:
    place_bounding_box = bounding_box(place_obj)
    # player needs to be within one of the interact boxes and facing the object to interact
    # these place objects can only be accessed from the north side e.g. cart returns
    interact_box = copy.deepcopy(place_bounding_box)
    interact_box['southmost'] = interact_box['northmost']
    interact_box['northmost'] -= interact_distance
    interact_box['player_needs_to_face'] = Direction.SOUTH
    return {'NORTH_BOX':interact_box}

def two_side_interact_area(place_obj) -> list:
    place_bounding_box = bounding_box(place_obj)
    # player needs to be within one of the interact boxes and facing the object to interact
    # these place objects can only be accessed from two sides
    interact_boxes = one_side_interact_area(place_obj)
    south_interact_box = copy.deepcopy(place_bounding_box)
    south_interact_box['northmost'] = place_bounding_box['southmost']
    south_interact_box['southmost'] += interact_distance
    south_interact_box['player_needs_to_face'] = Direction.NORTH
    interact_boxes['SOUTH_BOX'] = south_interact_box
    return interact_boxes

def four_side_interact_area(place_obj:dict) -> dict:
    place_bounding_box = bounding_box(place_obj)
    # player needs to be within interact box to interact
    interact_boxes = two_side_interact_area(place_obj)
    west_interact_box = copy.deepcopy(place_bounding_box)
    west_interact_box['eastmost'] = place_bounding_box['westmost']
    west_interact_box['westmost'] -= interact_distance
    west_interact_box['player_needs_to_face'] = Direction.EAST
    east_interact_box = copy.deepcopy(place_bounding_box)
    east_interact_box['westmost'] = place_bounding_box['eastmost']
    east_interact_box['eastmost'] += interact_distance
    east_interact_box['player_needs_to_face'] = Direction.WEST
    interact_boxes['WEST_BOX'] = west_interact_box
    interact_boxes['EAST_BOX'] = east_interact_box
    return interact_boxes

def obj_overlap_with_box(obj:dict, box:dict):
   obj['bounding_box'] = bounding_box(place=obj)
   return not (
            obj['bounding_box']['westmost'] > box['eastmost'] or\
            obj['bounding_box']['northmost'] > box['southmost'] or\
            obj['bounding_box']['eastmost'] < box['westmost'] or\
            obj['bounding_box']['southmost'] < box['northmost']
        )


def can_interact_in_box(player, interact_box) -> bool:
    """Returns whether `player` overlaps with interact_box

    Args:
        player (dict): player
        interact_box (dict): interact box

    Returns:
        bool: Whether the player can interact in box
    """
    player['bounding_box'] = bounding_box(place=player)
    if obj_overlap_with_box(obj=player, box=interact_box) and player['direction'] == interact_box['player_needs_to_face'].value:
        return True
    return False

def can_interact_player(player, place_obj) -> bool:
    """Returns whether the `player` object can interact with the `place_obj` based on their interact boxes

    Args:
        player (dict): a player dictionary containing the player's interact boxes
        place_obj (dict): a place object containing the place's interact boxes

    Returns:
        bool: whether the player and the place can interact
    """
    for interact_box in place_obj['interact_boxes']:
        if obj_overlap_with_box(obj=player, box=interact_box) and player_directions[player['direction']] == interact_box['player_needs_to_face']:
            return True
    return False

def loc_in_interact_box(box, loc) -> bool:
    return (
        box['northmost'] <= loc[1] <= box['southmost'] and box['westmost'] <= loc[0] <= box['eastmost']
    )

def x_in_interact_box(box, x) -> bool:
    return (
       box['westmost'] <= x <= box['eastmost']
    )

def y_in_interact_box(box, y) -> bool:
    return (
       box['northmost'] <= y <= box['southmost']
    )


def add_interact_boxes_to_obs(obs) -> dict:
    """Add interact boxes to objects in the observation

    Args:
        obs (dict): the observation dictionary

    Returns:
        dict: obs with interact boxes added to its obejcts
    """
    for object_name in obs:
        object_list = obs[object_name]
        for _, obj_dict in enumerate(object_list):
            if object_name == 'players':
                obj_dict['bounding_box'] = bounding_box(obj_dict)
            elif object_name == "cartReturns":
                obj_dict["interact_boxes"] = one_side_interact_area(obj_dict)
            elif object_name == "baskets":
                obj_dict["interact_boxes"] = four_side_interact_area(obj_dict)
            elif object_name == "carts":
                possible_boxes = four_side_interact_area(obj_dict)
                obj_dir = obj_dict['direction']
                if obj_dir == Direction.NORTH:#can be interacted with from the SOUTH
                    obj_dict["interact_boxes"] = {'SOUTH_BOX':possible_boxes['SOUTH_BOX']}
                elif obj_dir == Direction.SOUTH:#can be interacted with from the NORTH
                    obj_dict["interact_boxes"] = {'NORTH_BOX':possible_boxes['NORTH_BOX']}
                elif obj_dir == Direction.WEST:#can be interacted with from the EAST
                    obj_dict["interact_boxes"] = {'EAST_BOX':possible_boxes['EAST_BOX']}
                else:#can be interacted with from the WEST
                    obj_dict["interact_boxes"] = {'WEST_BOX':possible_boxes['SOUTH_BOX']}
            elif object_name == "shelves":
                obj_dict['interact_boxes'] = two_side_interact_area(obj_dict)
            else:
                obj_dict["interact_boxes"] = four_side_interact_area(obj_dict)
    return obs

if __name__ == "__main__":
    # run this to test adding interact boxes to objects in env.json (json version of the env object)
    # Get the path to the current file
    current_file_path = Path(__file__)

    # Get the folder containing the current file
    dir = current_file_path.parent
    f = open(dir / "env.json")
    obs = json.load(f)
    # test adding interact boxes to each object in the environment
    obs = add_interact_boxes_to_obs(obs)
    with open(dir / 'env_interact_boxes.json', 'w') as file:
    # Write the dictionary to the JSON file
        json.dump(obs, file, indent=4)


