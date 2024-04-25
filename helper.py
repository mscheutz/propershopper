import decimal
import math
from copy import deepcopy
from final_proj.constants import *
from enums.direction import Direction


def obj_collision(obj, x_position, y_position, x_margin=0.55, y_margin=0.55):
    return obj.position[0] - x_margin < x_position < obj.position[0] + obj.width + x_margin and \
        obj.position[1] - y_margin < y_position < obj.position[1] + obj.height + y_margin


def overlap(x1, y1, width_1, height_1, x2, y2, width_2, height_2):
    return not (x1 > x2 + width_2 or x2 > x1 + width_1 or y1 > y2 + height_2 or y2 > y1 + height_1)


def objects_overlap(obj1, obj2):
    return overlap(obj1['position'][0], obj1['position'][1], obj1['width'], obj1['height'],
                   obj2['position'][0], obj2['position'][1], obj2['width'], obj2['height'])


def pos_collision(x1, y1, x2, y2, x_margin, y_margin):
    return x1 - x_margin < x2 < x1 + x_margin and y1 - y_margin < y2 < y1 + y_margin


def can_interact_default(obj, player, range=0.5):
    if player.direction == Direction.NORTH:
        return obj.collision(player, player.position[0], player.position[1] - range)
    elif player.direction == Direction.SOUTH:
        return obj.collision(player, player.position[0], player.position[1] + range)
    elif player.direction == Direction.WEST:
        return obj.collision(player, player.position[0] - range, player.position[1])
    elif player.direction == Direction.EAST:
        return obj.collision(player, player.position[0] + range, player.position[1])
    return False



def project_collision_with_orientation(obj, state, direction: Direction, dist=0.4, buffer=0.0):#orientation matters
    """Project collision while taking the obj's orientation into account. This should only be used when the player is very close to the target item they want to interact with. Otherwise, the player might get stuck turning back and forth in a corner formed by static obstacles 

    Args:
        obj (dict): most likely the player
        state (dict): game state
        direction (Direction): directional command
        dist (float, optional): distance the obj is about to travel. Defaults to 0.4.
        buffer (float, optional): buffer between objects in the env. Defaults to 0.0.

    Returns:
        _type_: _description_
    """
    obj_copy = deepcopy(obj)

    if direction == Direction.NORTH:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][1] -= dist
        if obj_copy['position'][1] < 2.1:
            return True
    elif direction == Direction.EAST:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][0] += dist
        if obj_copy['position'][0] > 18.5:
            return True
    elif direction == Direction.SOUTH:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][1] += dist
        if obj_copy['position'][1] > 24:
            return True
    elif direction == Direction.WEST:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][0] -= dist
        if obj_copy['position'][0] < 0.55:
            return True

    for key, value in state['observation'].items():
        for item in value:
            if key == 'players':#for players, pretend that they are wider and taller than they actually are to stay away
                if (obj_copy == item or (
                        'index' in item.keys() and 'index' in obj_copy.keys() and item['index'] == obj_copy['index'])):
                    continue
                if (overlap(obj_copy['position'][0], obj_copy['position'][1], obj_copy['width'], obj_copy['height'],
                            item['position'][0], item['position'][1], item['width'] + buffer + 0.75, item['height'] + buffer + 0.75)):
                    return True
            else:
                if (obj_copy == item or (
                        'index' in item.keys() and 'index' in obj_copy.keys() and item['index'] == obj_copy['index'])):
                    continue
                if (overlap(obj_copy['position'][0], obj_copy['position'][1], obj_copy['width'], obj_copy['height'],
                            item['position'][0], item['position'][1], item['width'] + buffer, item['height'] + buffer)):
                    return True
    return False

def project_collision(obj, state, direction: Direction, dist=0.4, buffer=0.0):
    """Project collision. This should only be used when the player is likely far from the target item they want to interact with. Otherwise, the player might get stuck turning back and forth in a corner formed by static obstacles 

    Args:
        obj (dict): most likely the player
        state (dict): game state
        direction (Direction): directional command
        dist (float, optional): distance the obj is about to travel. Defaults to 0.4.
        buffer (float, optional): buffer between objects in the env. Defaults to 0.0.

    Returns:
        _type_: _description_
    """
    obj_copy = deepcopy(obj)

    if direction == Direction.NORTH:
        obj_copy['position'][1] -= dist
        if obj_copy['position'][1] < 2.1:
            return True
    elif direction == Direction.EAST:
        obj_copy['position'][0] += dist
        if obj_copy['position'][0] > 18.5:
            return True
    elif direction == Direction.SOUTH:
        obj_copy['position'][1] += dist
        if obj_copy['position'][1] > 24:
            return True
    elif direction == Direction.WEST:
        obj_copy['position'][0] -= dist
        if obj_copy['position'][0] < 0.55:
            return True

    for key, value in state['observation'].items():
        for item in value:
            if key == 'players':#for players, pretend that they are wider and taller than they actually are to stay away
                if (obj_copy == item or (
                        'index' in item.keys() and 'index' in obj_copy.keys() and item['index'] == obj_copy['index'])):
                    continue
                if (overlap(obj_copy['position'][0], obj_copy['position'][1], obj_copy['width'], obj_copy['height'],
                            item['position'][0], item['position'][1], item['width'] + buffer + 0.75, item['height'] + buffer + 0.75)):
                    return True
            else:
                if (obj_copy == item or (
                        'index' in item.keys() and 'index' in obj_copy.keys() and item['index'] == obj_copy['index'])):
                    continue
                if (overlap(obj_copy['position'][0], obj_copy['position'][1], obj_copy['width'], obj_copy['height'],
                            item['position'][0], item['position'][1], item['width'] + buffer, item['height'] + buffer)):
                    return True
    return False


def project_collision_dyn(obj, state, direction: Direction, dist=0.4, buffer=0):
    obj_copy = deepcopy(obj)

    if direction == Direction.NORTH:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][1] -= dist
        if obj_copy['position'][1] < 2.1:
            return True
    elif direction == Direction.EAST:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][0] += dist
        if obj_copy['position'][0] > 18.5:
            return True
    elif direction == Direction.SOUTH:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][1] += dist
        if obj_copy['position'][1] > 24:
            return True
    elif direction == Direction.WEST:
        if obj_copy['direction'] == direction.value:#object moves
            obj_copy['position'][0] -= dist
        if obj_copy['position'][0] < 0.55:
            return True

    for key, value in state['observation'].items():
        for item in value:
            if (overlap(obj_copy['position'][0], obj_copy['position'][1], obj_copy['width'], obj_copy['height'],
                        item['position'][0] - buffer, item['position'][1] - buffer, item['width'] + buffer,
                        item['height'] + buffer)):
                if not (obj_copy == item or (
                        'index' in item.keys() and 'index' in obj_copy.keys() and item['index'] == obj_copy['index'])):
                    if key == "players":
                        return -1
                    else:
                        return -1
    return 0


def round_float(n, granularity):
    d = decimal.Decimal(str(granularity))
    precision = -1 * d.as_tuple().exponent
    return round(round(n / granularity) * granularity, precision)


def euclidean_distance(pos1, pos2):
    # Calculate Euclidean distance between two points
    return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
