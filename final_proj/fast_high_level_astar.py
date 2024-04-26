
import numpy as np
import json
from queue import PriorityQueue

import json
import socket


from util import *
from box_regions import *

cartReturns = [2, 18.5]
basketReturns = [3.5, 18.5]
registerReturns_1 = [2, 4.5]
registerReturns_2 = [2, 9.5]

offset = 1

objs = [
    {'height': 2.5, 'width': 3, 'position': [0.2, 4.5], 're_centered_position': [2.125, 5.75]},
    {'height': 2.5, 'width': 3, 'position': [0.2, 9.5], 're_centered_position': [2.125, 10.75]},
    {'height': 1, 'width': 2, 'position': [5.5, 1.5], 're_centered_position': [6.5, 2]},
    {'height': 1, 'width': 2, 'position': [7.5, 1.5], 're_centered_position': [8.5, 2]},
    {'height': 1, 'width': 2, 'position': [9.5, 1.5], 're_centered_position': [10.5, 2]},
    {'height': 1, 'width': 2, 'position': [11.5, 1.5], 're_centered_position': [12.5, 2]},
    {'height': 1, 'width': 2, 'position': [13.5, 1.5], 're_centered_position': [14.5, 2]},
    {'height': 1, 'width': 2, 'position': [5.5, 5.5], 're_centered_position': [6.5, 6]},
    {'height': 1, 'width': 2, 'position': [7.5, 5.5], 're_centered_position': [8.5, 6]},
    {'height': 1, 'width': 2, 'position': [9.5, 5.5], 're_centered_position': [10.5, 6]},
    {'height': 1, 'width': 2, 'position': [11.5, 5.5], 're_centered_position': [12.5, 6]},
    {'height': 1, 'width': 2, 'position': [13.5, 5.5], 're_centered_position': [14.5, 6]},
    {'height': 1, 'width': 2, 'position': [5.5, 9.5], 're_centered_position': [6.5, 10]},
    {'height': 1, 'width': 2, 'position': [7.5, 9.5], 're_centered_position': [8.5, 10]},
    {'height': 1, 'width': 2, 'position': [9.5, 9.5], 're_centered_position': [10.5, 10]},
    {'height': 1, 'width': 2, 'position': [11.5, 9.5], 're_centered_position': [12.5, 10]},
    {'height': 1, 'width': 2, 'position': [13.5, 9.5], 're_centered_position': [14.5, 10]},
    {'height': 1, 'width': 2, 'position': [5.5, 13.5], 're_centered_position': [6.5, 14]},
    {'height': 1, 'width': 2, 'position': [7.5, 13.5], 're_centered_position': [8.5, 14]},
    {'height': 1, 'width': 2, 'position': [9.5, 13.5], 're_centered_position': [10.5, 14]},
    {'height': 1, 'width': 2, 'position': [11.5, 13.5], 're_centered_position': [12.5, 14]},
    {'height': 1, 'width': 2, 'position': [13.5, 13.5], 're_centered_position': [14.5, 14]},
    {'height': 1, 'width': 2, 'position': [5.5, 17.5], 're_centered_position': [6.5, 18]},
    {'height': 1, 'width': 2, 'position': [7.5, 17.5], 're_centered_position': [8.5, 18]},
    {'height': 1, 'width': 2, 'position': [9.5, 17.5], 're_centered_position': [10.5, 18]},
    {'height': 1, 'width': 2, 'position': [11.5, 17.5], 're_centered_position': [12.5, 18]},
    {'height': 1, 'width': 2, 'position': [13.5, 17.5], 're_centered_position': [14.5, 18]},
    {'height': 1, 'width': 2, 'position': [5.5, 21.5], 're_centered_position': [6.5, 22]},
    {'height': 1, 'width': 2, 'position': [7.5, 21.5], 're_centered_position': [8.5, 22]},
    {'height': 1, 'width': 2, 'position': [9.5, 21.5], 're_centered_position': [10.5, 22]},
    {'height': 1, 'width': 2, 'position': [11.5, 21.5], 're_centered_position': [12.5, 22]},
    {'height': 1, 'width': 2, 'position': [13.5, 21.5], 're_centered_position': [14.5, 22]},
    {'height': 6, 'width': 0.7, 'position': [1, 18.5], 're_centered_position': [1.35, 21.5]},
    {'height': 6, 'width': 0.7, 'position': [2, 18.5], 're_centered_position': [2.35, 21.5]},
    {'height': 0.8, 'width': 0.8, 'position': [3.5, 18.5], 're_centered_position': [4.15, 19.4]},
    {'height': 2.25, 'width': 1.5, 'position': [18.25, 4.75], 're_centered_position': [19.125, 5.875]},
    {'height': 2.25, 'width': 1.5, 'position': [18.25, 10.75], 're_centered_position': [19.125, 11.875]}
]


def update_position_to_center(obj_pose):
    """
    Update the position of objects to their re_centered_position if their current position matches obj_pose.

    Parameters:
        objects (list of dicts): List of objects with details including position and re_centered_position.
        obj_pose (list): The position to match for updating to re_centered_position.
    
    Returns:
        None: Objects are modified in place.
    """
    global objs
    for obj in objs:
        # Compare current position with obj_pose
        if obj['position'] == obj_pose:
            # If they match, update position to re_centered_position
            obj_pose = obj['re_centered_position']
            break
    return obj_pose


class Astar_agent:
    def __init__(self, socket_game, env):
        self.shopping_list = env['observation']['players'][0]['shopping_list']
        self.shopping_quant = env['observation']['players'][0]['list_quant']
        self.game = socket_game
        self.map_width = 20
        self.map_height = 25
        self.obs = env['observation']
        self.cart = None
        self.basket = None
        self.player = self.obs['players'][0]
        self.last_action = "NOP"
        self.current_direction = self.player['direction']
        self.size = [0.6, 0.4]
    

    
    # def collision(self, x, y, width, height, obj):
    #     """
    #     Check if a rectangle defined by (x, y, width, height) does NOT intersect with an object
    #     and ensure the rectangle stays within the map boundaries.

    #     Parameters:
    #         x (float): The x-coordinate of the rectangle's top-left corner.
    #         y (float): The y-coordinate of the rectangle's top-left corner.
    #         width (float): The width of the rectangle.
    #         height (float): The height of the rectangle.
    #         obj (dict): An object with 'position', 'width', and 'height'.

    #     Returns:
    #         bool: Returns True if there is NO collision (i.e., no overlap) and the rectangle is within map boundaries,
    #             False if there is a collision or the rectangle goes outside the map boundaries.
    #     """
    #     # Define map boundaries
    #     min_x = 0.5
    #     max_x = 24
    #     min_y = 2.5
    #     max_y = 19.5

    #     # Calculate the boundaries of the rectangle
    #     rectangle = {
    #         'northmost': y,
    #         'southmost': y + height,
    #         'westmost': x,
    #         'eastmost': x + width
    #     }
        
    #     # Ensure the rectangle is within the map boundaries
    #     if not (min_x <= rectangle['westmost'] and rectangle['eastmost'] <= max_x and
    #             min_y <= rectangle['northmost'] and rectangle['southmost'] <= max_y):
    #         return False  # The rectangle is out of the map boundaries

    #     # Calculate the boundaries of the object
    #     obj_box = {
    #         'northmost': obj['position'][1],
    #         'southmost': obj['position'][1] + obj['height'],
    #         'westmost': obj['position'][0],
    #         'eastmost': obj['position'][0] + obj['width']
    #     }

    #     # Check if there is no overlap using the specified cardinal bounds
    #     no_overlap = not (
    #         (obj_box['northmost'] <= rectangle['northmost'] <= obj_box['southmost'] or
    #         obj_box['northmost'] <= rectangle['southmost'] <= obj_box['southmost']) and (
    #             (obj_box['westmost'] <= rectangle['westmost'] <= obj_box['eastmost'] or
    #             obj_box['westmost'] <= rectangle['eastmost'] <= obj_box['eastmost'])
    #         )
    #     )
        
    #     return no_overlap

    # # The function will return False if the rectangle is outside the map boundaries or intersects with the object.
    

    # def hits_wall(self, x, y):
    #     wall_width = 0.4
    #     return (y <= 2 or y + self.size[1] >= self.map_height - wall_width or \
    #             x + self.size[0] >= self.map_width - wall_width) 

    
    def is_close_enough(self, current, goal:tuple|dict, tolerance=0.15, is_item = True):
        """Check if the current position is within tolerance of the goal position."""
        if is_item:
            tolerance = 0.6
            return (abs(current[0] - goal[0]) < tolerance - 0.15  and abs(current[1] - goal[1]) < tolerance +0.05 )

        else:
            return (abs(current[0] - goal[0]) < tolerance and abs(current[1] - goal[1]) < tolerance)

    
    def which_region(self, location:list|tuple) -> BoxRegion:
        """Find which region the location is in

        Args:
            location (list | tuple): (x, y)

        Returns:
            BoxRegion: the region location is in
        """
        for box_region in regions:
            if box_region.contains(location):
                return box_region
        raise Exception("location not on map")

    
    def normalized_manhattan_dist(self, start:tuple|list, goal:tuple|list) -> float:
        """Return the normalized manhattan dist from start to goal

        Args:
            start (tuple | list): (x, y)
            goal (tuple | list): (x, y)

        Returns:
            float: between 0 and 1
        """
        longest_possible_manhattan_dist = MAP_WIDTH + MAP_HEIGHT
        dist = manhattan_distance(pos1=start, pos2=goal)
        return dist / longest_possible_manhattan_dist
    
    def heuristic(self, box_region:BoxRegion, goal:list|tuple) -> float:
        return self.normalized_manhattan_dist(start=box_region.midpoint, goal=goal)

    
    def astar(self, player, start, goal, obs):
        """Perform high level planning to find a path from start location to goal region."""
        start_region = self.which_region(start) # figure out which BoxRegion start is in
        frontier = PriorityQueue()
        frontier.put(start_region, 0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start_region] = 0

   
        while not frontier.empty():
            curr_region:BoxRegion = frontier.get()
            if curr_region.contains(goal):
                break # found goal region
            for neighbor_region in curr_region.neighbors:
                cost_to_neighbor = cost_so_far[curr_region] + 1 + calculate_crowdedness_factor(player, neighbor_region, obs)
                if neighbor_region not in cost_so_far or cost_so_far[neighbor_region] > cost_to_neighbor:
                    cost_so_far[neighbor_region] = cost_to_neighbor
                    priority = cost_to_neighbor + self.heuristic(neighbor_region, goal)
                    frontier.put(neighbor_region, priority)
                    came_from[neighbor_region] = curr_region
            
        # Reconstruct path
        path = []
        while current:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    
def find_item_position(data, item_name):
    """
    Finds the position of an item based on its name within the shelves section of the data structure.

    Parameters:
        data (dict): The complete data structure containing various game elements including shelves.
        item_name (str): The name of the item to find.

    Returns:
        list or None: The position of the item as [x, y] or None if the item is not found.
    """
    # Loop through each shelf in the data
    for shelf in data['observation']['shelves']:
        if shelf['food_name'] == item_name:
            return shelf['position']
    return None

# {'command_result': {'command': 'RESET', 'result': 'SUCCESS', 'message': '', 'stepCost': 0}, 'observation': {'players': [{'index': 0, 'position': [1.2, 15.6], 'width': 0.6, 'height': 0.4, 'sprite_path': None, 'direction': 2, 'curr_cart': -1, 'shopping_list': ['chocolate milk'], 'list_quant': [1], 'holding_food': None, 'bought_holding_food': False, 'budget': 100, 'bagged_items': [], 'bagged_quant': []}], 'carts': [], 'baskets': [], 'registers': [{'height': 2.5, 'width': 2.25, 'position': [1, 4.5], 'num_items': 0, 'foods': [], 'food_quantities': [], 'food_images': [], 'capacity': 12, 'image': 'images/Registers/registersA.png', 'curr_player': None}, {'height': 2.5, 'width': 2.25, 'position': [1, 9.5], 'num_items': 0, 'foods': [], 'food_quantities': [], 'food_images': [], 'capacity': 12, 'image': 'images/Registers/registersB.png', 'curr_player': None}], 'shelves': [{'height': 1, 'width': 2, 'position': [5.5, 1.5], 'food': 'milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'milk'}, {'height': 1, 'width': 2, 'position': [7.5, 1.5], 'food': 'milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'milk'}, {'height': 1, 'width': 2, 'position': [9.5, 1.5], 'food': 'chocolate milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk_chocolate.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'chocolate milk'}, {'height': 1, 'width': 2, 'position': [11.5, 1.5], 'food': 'chocolate milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk_chocolate.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'chocolate milk'}, {'height': 1, 'width': 2, 'position': [13.5, 1.5], 'food': 'strawberry milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk_strawberry.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'strawberry milk'}, {'height': 1, 'width': 2, 'position': [5.5, 5.5], 'food': 'apples', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/apples.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'apples'}, {'height': 1, 'width': 2, 'position': [7.5, 5.5], 'food': 'oranges', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/oranges.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'oranges'}, {'height': 1, 'width': 2, 'position': [9.5, 5.5], 'food': 'banana', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/banana.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'banana'}, {'height': 1, 'width': 2, 'position': [11.5, 5.5], 'food': 'strawberry', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/strawberry.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'strawberry'}, {'height': 1, 'width': 2, 'position': [13.5, 5.5], 'food': 'raspberry', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/raspberry.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'raspberry'}, {'height': 1, 'width': 2, 'position': [5.5, 9.5], 'food': 'sausage', 'price': 4, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/sausage.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'sausage'}, {'height': 1, 'width': 2, 'position': [7.5, 9.5], 'food': 'steak', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/meat_01.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'steak'}, {'height': 1, 'width': 2, 'position': [9.5, 9.5], 'food': 'steak', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/meat_02.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'steak'}, {'height': 1, 'width': 2, 'position': [11.5, 9.5], 'food': 'chicken', 'price': 6, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/meat_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'chicken'}, {'height': 1, 'width': 2, 'position': [13.5, 9.5], 'food': 'ham', 'price': 6, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/ham.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'ham'}, {'height': 1, 'width': 2, 'position': [5.5, 13.5], 'food': 'brie cheese', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_01.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'brie cheese'}, {'height': 1, 'width': 2, 'position': [7.5, 13.5], 'food': 'swiss cheese', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_02.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'swiss cheese'}, {'height': 1, 'width': 2, 'position': [9.5, 13.5], 'food': 'cheese wheel', 'price': 15, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cheese wheel'}, {'height': 1, 'width': 2, 'position': [11.5, 13.5], 'food': 'cheese wheel', 'price': 15, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cheese wheel'}, {'height': 1, 'width': 2, 'position': [13.5, 13.5], 'food': 'cheese wheel', 'price': 15, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cheese wheel'}, {'height': 1, 'width': 2, 'position': [5.5, 17.5], 'food': 'garlic', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/garlic.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'garlic'}, {'height': 1, 'width': 2, 'position': [7.5, 17.5], 'food': 'leek', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/leek_onion.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'leek'}, {'height': 1, 'width': 2, 'position': [9.5, 17.5], 'food': 'red bell pepper', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/bell_pepper_red.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'red bell pepper'}, {'height': 1, 'width': 2, 'position': [11.5, 17.5], 'food': 'carrot', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/carrot.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'carrot'}, {'height': 1, 'width': 2, 'position': [13.5, 17.5], 'food': 'lettuce', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/lettuce.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'lettuce'}, {'height': 1, 'width': 2, 'position': [5.5, 21.5], 'food': 'avocado', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/avocado.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'avocado'}, {'height': 1, 'width': 2, 'position': [7.5, 21.5], 'food': 'broccoli', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/broccoli.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'broccoli'}, {'height': 1, 'width': 2, 'position': [9.5, 21.5], 'food': 'cucumber', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cucumber.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cucumber'}, {'height': 1, 'width': 2, 'position': [11.5, 21.5], 'food': 'yellow bell pepper', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/bell_pepper_yellow.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'yellow bell pepper'}, {'height': 1, 'width': 2, 'position': [13.5, 21.5], 'food': 'onion', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/onion.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'onion'}], 'cartReturns': [{'height': 6, 'width': 0.7, 'position': [1, 18.5], 'quantity': 6}, {'height': 6, 'width': 0.7, 'position': [2, 18.5], 'quantity': 6}], 'basketReturns': [{'height': 0.2, 'width': 0.3, 'position': [3.5, 18.5], 'quantity': 12}], 'counters': [{'height': 2.25, 'width': 1.5, 'position': [18.25, 4.75], 'food': 'prepared foods', 'price': 15}, {'height': 2.25, 'width': 1.5, 'position': [18.25, 10.75], 'food': 'fresh fish', 'price': 12}, {'height': 2.25, 'width': 1.5, 'position': [18.25, 10.75], 'food': 'fresh fish', 'price': 12}]}, 'step': 1, 'gameOver': False, 'violations': ''}
# [11.5, 17.5]
# hang@jstaley-XPS-8940:~/TA/propershopper-1$ python astar_path_planner.py 
# action_commands:  ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']
# ['sausage', 'milk', 'prepared foods', 'onion', 'fresh fish', 'apples', 'oranges', 'steak']
# {'command_result': {'command': 'RESET', 'result': 'SUCCESS', 'message': '', 'stepCost': 0}, 'observation': {'players': [{'index': 0, 'position': [1.2, 15.6], 'width': 0.6, 'height': 0.4, 'sprite_path': None, 'direction': 2, 'curr_cart': -1, 'shopping_list': ['sausage', 'milk', 'prepared foods', 'onion', 'fresh fish', 'apples', 'oranges', 'steak'], 'list_quant': [2, 3, 1, 1, 1, 1, 1, 1], 'holding_food': None, 'bought_holding_food': False, 'budget': 100, 'bagged_items': [], 'bagged_quant': []}], 'carts': [], 'baskets': [], 'registers': [{'height': 2.5, 'width': 2.25, 'position': [1, 4.5], 'num_items': 0, 'foods': [], 'food_quantities': [], 'food_images': [], 'capacity': 12, 'image': 'images/Registers/registersA.png', 'curr_player': None}, {'height': 2.5, 'width': 2.25, 'position': [1, 9.5], 'num_items': 0, 'foods': [], 'food_quantities': [], 'food_images': [], 'capacity': 12, 'image': 'images/Registers/registersB.png', 'curr_player': None}], 'shelves': [{'height': 1, 'width': 2, 'position': [5.5, 1.5], 'food': 'milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'milk'}, {'height': 1, 'width': 2, 'position': [7.5, 1.5], 'food': 'milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'milk'}, {'height': 1, 'width': 2, 'position': [9.5, 1.5], 'food': 'chocolate milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk_chocolate.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'chocolate milk'}, {'height': 1, 'width': 2, 'position': [11.5, 1.5], 'food': 'chocolate milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk_chocolate.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'chocolate milk'}, {'height': 1, 'width': 2, 'position': [13.5, 1.5], 'food': 'strawberry milk', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/milk_strawberry.png', 'shelf_image': 'images/Shelves/fridge.png', 'food_name': 'strawberry milk'}, {'height': 1, 'width': 2, 'position': [5.5, 5.5], 'food': 'apples', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/apples.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'apples'}, {'height': 1, 'width': 2, 'position': [7.5, 5.5], 'food': 'oranges', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/oranges.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'oranges'}, {'height': 1, 'width': 2, 'position': [9.5, 5.5], 'food': 'banana', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/banana.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'banana'}, {'height': 1, 'width': 2, 'position': [11.5, 5.5], 'food': 'strawberry', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/strawberry.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'strawberry'}, {'height': 1, 'width': 2, 'position': [13.5, 5.5], 'food': 'raspberry', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/raspberry.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'raspberry'}, {'height': 1, 'width': 2, 'position': [5.5, 9.5], 'food': 'sausage', 'price': 4, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/sausage.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'sausage'}, {'height': 1, 'width': 2, 'position': [7.5, 9.5], 'food': 'steak', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/meat_01.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'steak'}, {'height': 1, 'width': 2, 'position': [9.5, 9.5], 'food': 'steak', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/meat_02.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'steak'}, {'height': 1, 'width': 2, 'position': [11.5, 9.5], 'food': 'chicken', 'price': 6, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/meat_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'chicken'}, {'height': 1, 'width': 2, 'position': [13.5, 9.5], 'food': 'ham', 'price': 6, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/ham.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'ham'}, {'height': 1, 'width': 2, 'position': [5.5, 13.5], 'food': 'brie cheese', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_01.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'brie cheese'}, {'height': 1, 'width': 2, 'position': [7.5, 13.5], 'food': 'swiss cheese', 'price': 5, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_02.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'swiss cheese'}, {'height': 1, 'width': 2, 'position': [9.5, 13.5], 'food': 'cheese wheel', 'price': 15, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cheese wheel'}, {'height': 1, 'width': 2, 'position': [11.5, 13.5], 'food': 'cheese wheel', 'price': 15, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cheese wheel'}, {'height': 1, 'width': 2, 'position': [13.5, 13.5], 'food': 'cheese wheel', 'price': 15, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cheese_03.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cheese wheel'}, {'height': 1, 'width': 2, 'position': [5.5, 17.5], 'food': 'garlic', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/garlic.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'garlic'}, {'height': 1, 'width': 2, 'position': [7.5, 17.5], 'food': 'leek', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/leek_onion.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'leek'}, {'height': 1, 'width': 2, 'position': [9.5, 17.5], 'food': 'red bell pepper', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/bell_pepper_red.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'red bell pepper'}, {'height': 1, 'width': 2, 'position': [11.5, 17.5], 'food': 'carrot', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/carrot.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'carrot'}, {'height': 1, 'width': 2, 'position': [13.5, 17.5], 'food': 'lettuce', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/lettuce.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'lettuce'}, {'height': 1, 'width': 2, 'position': [5.5, 21.5], 'food': 'avocado', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/avocado.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'avocado'}, {'height': 1, 'width': 2, 'position': [7.5, 21.5], 'food': 'broccoli', 'price': 1, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/broccoli.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'broccoli'}, {'height': 1, 'width': 2, 'position': [9.5, 21.5], 'food': 'cucumber', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/cucumber.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'cucumber'}, {'height': 1, 'width': 2, 'position': [11.5, 21.5], 'food': 'yellow bell pepper', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/bell_pepper_yellow.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'yellow bell pepper'}, {'height': 1, 'width': 2, 'position': [13.5, 21.5], 'food': 'onion', 'price': 2, 'capacity': 12, 'quantity': 12, 'food_image': 'images/food/onion.png', 'shelf_image': 'images/Shelves/shelf.png', 'food_name': 'onion'}], 'cartReturns': [{'height': 6, 'width': 0.7, 'position': [1, 18.5], 'quantity': 6}, {'height': 6, 'width': 0.7, 'position': [2, 18.5], 'quantity': 6}], 'basketReturns': [{'height': 0.2, 'width': 0.3, 'position': [3.5, 18.5], 'quantity': 12}], 'counters': [{'height': 2.25, 'width': 1.5, 'position': [18.25, 4.75], 'food': 'prepared foods', 'price': 15}, {'height': 2.25, 'width': 1.5, 'position': [18.25, 10.75], 'food': 'fresh fish', 'price': 12}, {'height': 2.25, 'width': 1.5, 'position': [18.25, 10.75], 'food': 'fresh fish', 'price': 12}]}, 'step': 1, 'gameOver': False, 'violations': ''}
# [11.5, 17.5]

if __name__=="__main__":

    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']

    print("action_commands: ", action_commands)

        # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))
    sock_game.send(str.encode("0 RESET"))  # reset the game
    state = recv_socket_data(sock_game)
    game_state = json.loads(state)
    shopping_list = game_state['observation']['players'][0]['shopping_list']
    shopping_quant = game_state['observation']['players'][0]['list_quant']
    agent = Astar_agent(socket_game=sock_game, env=game_state)
    print(shopping_list)


    # shopping_list = ['fresh fish', 'prepared foods']

        

