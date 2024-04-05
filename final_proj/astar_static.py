import math
from copy import deepcopy

import numpy as np
from PIL import Image

from enums.direction import Direction
from helper import project_collision_dyn, project_collision

from warnings import warn
import heapq

STEP = 0.3
BUFFER = 0.3


def init_map(obs):
    map_ = []
    tile = {
        "position": [0, 0],
        "width": 0.6,
        "height": 0.4,
        "index": 0
    }
    max_width = 25
    max_height = 25
    while tile["position"][1] < max_height:
        map_.append([])
        while tile["position"][0] < max_width:
            map_[len(map_) - 1].append(project_collision_dyn(tile, obs, Direction.NONE, buffer=BUFFER))
            tile["position"][0] += STEP

        tile["position"][0] = 0
        tile["position"][1] += STEP

    # map_ = update_dyn(map_, obs)

    x = np.asarray(map_, np.uint8)
    im = Image.fromarray(x, 'P')
    im.putpalette([0, 0, 0,  # Black
                   255, 0, 0,  # Red
                   0, 255, 0,  # g
                   0, 255, 255])  # b
    im.show()

    return map_


def update_dyn(map_: [[]], state, index=0):
    for player in state['observation']['players']:
        if player['index'] == index:
            continue
        x = round((player['position'][0] - BUFFER) / STEP)
        y = round((player['position'][1] - BUFFER) / STEP)
        for i in range(math.ceil((player['width'] + BUFFER) / STEP)):
            for j in range(math.ceil((player['height'] + BUFFER) / STEP)):
                map_[y + j][x + i] = -1
    return map_


class Node:
    """
    A node class for A* Pathfinding
    """

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

    def __repr__(self):
        return f"{self.position} - g: {self.g} h: {self.h} f: {self.f}"

    # defining less than for purposes of heap queue
    def __lt__(self, other):
        return self.f < other.f

    # defining greater than for purposes of heap queue
    def __gt__(self, other):
        return self.f > other.f


def return_path(current_node):
    path = []
    current = current_node
    while current is not None:
        path.append(current.position)
        current = current.parent
    return path[::-1]  # Return reversed path


def astar(goal, player, maze):
    start = (round(player['position'][1] / STEP), round(player['position'][0] / STEP))
    end = (round(goal['position'][1] / STEP), round(goal['position'][0] / STEP))

    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Heapify the open_list and Add the start node
    heapq.heapify(open_list)
    heapq.heappush(open_list, start_node)

    # Adding a stop condition
    outer_iterations = 0
    max_iterations = (len(maze[0]) * len(maze) // 2)

    # what squares do we search
    adjacent_squares = ((0, -1), (0, 1), (-1, 0), (1, 0),)

    # Loop until you find the end
    while len(open_list) > 0:
        outer_iterations += 1

        if outer_iterations > max_iterations:
            # if we hit this point return the path such as it is
            # it will not contain the destination
            warn("giving up on pathfinding too many iterations")
            return return_path(current_node)

            # Get the current node
        current_node = heapq.heappop(open_list)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            return return_path(current_node)

        # Generate children
        children = []

        for new_position in adjacent_squares:  # Adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure walkable terrain
            if maze[node_position[0]][node_position[1]] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:
            # Child is on the closed list
            if len([closed_child for closed_child in closed_list if closed_child == child]) > 0:
                continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + (
                    (child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            if len([open_node for open_node in open_list if
                    child.position == open_node.position and child.g > open_node.g]) > 0:
                continue

            # Add the child to the open list
            heapq.heappush(open_list, child)

    warn("Couldn't get a path to destination")
    return None


def convert_to_real(loc):
    return loc * STEP


def convert_to_index(loc):
    return round(loc / STEP)


def get_pathfind_index(obj):
    return f"{convert_to_index(obj['position'][1])},{convert_to_index(obj['position'][0])}"
