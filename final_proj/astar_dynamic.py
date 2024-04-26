import math
from copy import deepcopy

import numpy as np
from PIL import Image

from enums.direction import Direction
from helper import project_collision_dyn, project_collision, round_float

STEP = 0.15


class Node:
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position


# By Nicholas Swift via https://medium.com/@nicholas.w.swift/easy-a-star-pathfinding-7e6689c7f7b2
# Modifications by Marlow Fawn
def astar(goal, player, state):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""
    player_copy = deepcopy(player)
    goal_copy = deepcopy(goal)

    start = (round(player_copy['position'][1] / STEP), round(player_copy['position'][0] / STEP))
    end = (round(goal_copy['position'][1] / STEP), round(goal_copy['position'][0] / STEP))
    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    while len(open_list) > 0:

        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Return reversed path

        # Generate children
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # Adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure walkable terrain
            # todo: If holding cart, even bigger?
            # todo: update based on new_position
            player_copy['position'][0] = convert_to_real(node_position[0])
            player_copy['position'][1] = convert_to_real(node_position[1])
            if project_collision(player_copy, state, Direction.NONE):
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + (
                    (child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)


def convert_to_real(loc):
    return loc * STEP


def convert_to_astar(loc):
    return round(loc / STEP)
