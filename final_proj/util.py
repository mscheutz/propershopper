import time
import json
import copy
from constants import *
from copy import deepcopy
from constants import *


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
    return abs(pos2[0] - pos1[1]) + abs(pos2[1] - pos2[0])

def euclidean_distance(pos1, pos2):
    # Calculate Euclidean distance between two points
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5

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
    interact_box['player_needs_to_face'] = 'SOUTH'
    return [interact_box]

def two_side_interact_area(place_obj) -> list:
    place_bounding_box = bounding_box(place_obj)
    # player needs to be within one of the interact boxes and facing the object to interact
    # these place objects can only be accessed from two sides
    interact_boxes = one_side_interact_area(place_obj)
    south_interact_box = copy.deepcopy(place_bounding_box)
    south_interact_box['northmost'] = place_bounding_box['southmost']
    south_interact_box['southmost'] += interact_distance
    south_interact_box['player_needs_to_face'] = 'NORTH'
    interact_boxes = [interact_boxes[0], south_interact_box]
    return interact_boxes

def four_side_interact_area(place_obj:dict) -> dict:
    place_bounding_box = bounding_box(place_obj)
    # player needs to be within interact box to interact
    interact_boxes = two_side_interact_area(place_obj)
    west_interact_box = copy.deepcopy(place_bounding_box)
    west_interact_box['eastmost'] = place_bounding_box['westmost']
    west_interact_box['westmost'] -= interact_distance
    west_interact_box['player_needs_to_face'] = 'EAST'
    east_interact_box = copy.deepcopy(place_bounding_box)
    east_interact_box['westmost'] = place_bounding_box['eastmost']
    east_interact_box['eastmost'] += interact_distance
    east_interact_box['player_needs_to_face'] = 'WEST'
    interact_boxes.append(east_interact_box)
    interact_boxes.append(west_interact_box)
    return interact_boxes

def overlap(player, interact_box):
        return (
            interact_box['northmost'] <= player['bounding_box']['northmost'] <= interact_box['southmost'] and (
                (interact_box['westmost'] <= player['bounding_box']['westmost'] <= interact_box['eastmost']) 
                or 
                (interact_box['westmost'] <= player['bounding_box']['eastmost'] <= interact_box['eastmost'])
            )
            or
            interact_box['northmost'] <= player['bounding_box']['southmost'] <= interact_box['southmost'] and (
                (interact_box['westmost'] <= player['bounding_box']['westmost'] <= interact_box['eastmost']) 
                or 
                (interact_box['westmost'] <= player['bounding_box']['eastmost'] <= interact_box['eastmost'])
            )
        )

def can_interact_player(player, place_obj) -> bool:
    """Returns whether the `player` object can interact with the `place_obj` based on their interact boxes

    Args:
        player (dict): a player dictionary containing the player's interact boxes
        place_obj (dict): a place object containing the place's interact boxes

    Returns:
        bool: whether the player and the place can interact
    """
    for interact_box in place_obj['interact_boxes']:
        if overlap(player=player, interact_box=interact_box) and player_directions[player['direction']] == interact_box['player_needs_to_face']:
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
                obj_dir = player_directions[obj_dict['direction']]
                if obj_dir == 'NORTH':
                    obj_dict["interact_boxes"] = [possible_boxes[1]]
                elif obj_dir == 'SOUTH':
                    obj_dict["interact_boxes"] = [possible_boxes[0]]
                elif obj_dir == 'WEST':
                    obj_dict["interact_boxes"] = [possible_boxes[2]]
                else:
                    obj_dict["interact_boxes"] = [possible_boxes[3]]
            elif object_name == "shelves":
                obj_dict['interact_boxes'] = two_side_interact_area(obj_dict)
            else:
                obj_dict["interact_boxes"] = four_side_interact_area(obj_dict)
    return obs

if __name__ == "__main__":
    # run this to test adding interact boxes to objects in env.json (json version of the env object)
    f = open("env.json")
    obs = json.load(f)
    # test adding interact boxes to each object in the environment
    obs = add_interact_boxes_to_obs(obs)
    with open('env_interact_boxes.json', 'w') as file:
    # Write the dictionary to the JSON file
        json.dump(obs, file, indent=4)


