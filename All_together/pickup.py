import ujson as json
import random
import socket
import gymnasium as gym
from env import SupermarketEnv
from utils import recv_socket_data


# target_coordinates = {"carts": [2, [1, 18.00], [2,18.00]], "baskets": [1, [3.5, 18.00]], "fresh fish": [2, [16.60, 11.70], [16.60, 15.6]], "prepared foods": [2, [17.40, 3.75], [17.40, 7.80]],"checkout counter": [2, [3.60, 12.15], [3.60, 7.35]],"milk": [1, [7.35, 3.75]], "chocolate milk": [1, [11.25, 3.75]], "strawberry milk": [1, [14.25, 3.75]], "raspberry": [2, [14.40, 3.75], [14.40, 7.75]], "strawberry": [2, [12.15, 3.75], [12.15, 7.75]], "banana": [2, [10.20, 3.75], [10.20, 7.75]], "oranges": [2, [8.25, 3.75], [8.25, 7.75]], "apples": [2, [6.30, 3.75], [6.30, 7.75]], "ham": [2, [14.40, 11.75], [14.40, 7.75]], "chicken": [2, [12.15, 11.75], [12.15, 7.75]], "steak": [2, [9.20, 11.75], [9.20, 7.75]], "sausage": [2, [6.30, 11.75], [6.30, 7.75]], "brie cheese": [2, [6.30, 11.75], [6.30, 15.75]], "swiss cheese": [2, [8.25, 11.75], [8.25, 15.75]], "cheese wheel": [2, [12.15, 11.75], [12.15, 15.75]], "lettuce": [2, [14.40, 15.75], [14.40, 19.75]], "carrot": [2, [12.15, 15.75], [12.15, 19.75]], "red bell pepper": [2, [10.20, 15.75], [10.20, 19.75]], "leek": [2, [8.25, 15.75], [8.25, 19.75]], "garlic": [2, [6.30, 15.75], [6.30, 19.75]], "onion": [1, [14.40, 19.75]], "yellow bell pepper": [1, [12.15, 19.75]], "cucumber": [1, [10.20, 19.75]], "broccoli": [1, [8.25, 19.75]], "avocado": [1, [6.30, 19.75]], "exit": [2, [0.60, 7.20], [0.60, 3.30]]}
# ADD THE COUNTERS
# "fresh fish": [1, [17.40, 13.05]], "prepared foods": [1, [17.40, 7.05]]
# shopping_list = ['milk', 'cucumber', 'red bell pepper', 'onion', 'avocado', 'cheese wheel', 'brie cheese', 'steak', 'chicken', 'prepared foods', 'milk', 'strawberry milk', 'chocolate milk', 'fresh fish', 'prepared foods']
# shopping_list = ['leek','brie cheese', 'steak', 'milk']
starting_location = [1, 15.3]

def interacter(state, reordered_shopping_list, playerNumber):
    item_rows = [[2, "milk", "chocolate milk", "strawberry milk"], [5.8, "apples", "oranges", "banana", "strawberry", "raspberry"], [9.8, "ham", "chicken", "steak", "sausage"], [14, "brie cheese", "swiss cheese", "cheese wheel"], [17.8, "garlic", "leek", "red bell pepper", "carrot", "lettuce"], [21.8, "avocado", "broccoli", "cucumber", "yellow bell pepper", "onion"]]
    action_list = []
    north = str(playerNumber) + " NORTH"
    south = str(playerNumber) + " SOUTH"
    west = str(playerNumber) + " WEST"
    east = str(playerNumber) +  " EAST"
    toggle_cart = str(playerNumber) + " TOGGLE_CART"
    interact = str(playerNumber) + " INTERACT"
    # Gathers information
    item = reordered_shopping_list[0]
    i = 0
    agent_coordinates = state['observation']['players'][playerNumber]['position']
    # Check for cart vs basket
    has_cart = state['observation']['players'][playerNumber]['curr_cart']
    if has_cart == -1:
        has_cart = False
    else:
        has_cart = True

    special_interactions = ["checkout counter", "carts", "baskets"]
    horizontal_counter = ["fresh fish", "prepared foods"]
    if item not in special_interactions:
        # Regular shelf
        if item not in horizontal_counter:
            ind = 0
            # Finding the row the item is in
            while i < len(item_rows):
                if reordered_shopping_list[0] in item_rows[i]:
                    print(str(reordered_shopping_list[0])+" was found in row "+str(i))
                    ind = i
                i += 1
            # Check if above or below
            # If below shelf
            item_y = item_rows[ind][0]
            if agent_coordinates[1] > item_y:
                # Check for cart
                if has_cart:
                    # If cart, must put cart aside first
                    # Turn left, put cart down, turn back up, move 2 up, interact, turn down, move 2 down, turn left, interact, toggle cart
                    action_list.append([west, toggle_cart, north, north, north, north, north, north, north, north, north, interact, interact, south, south, south, south, south, south, south, south, south, west, interact, toggle_cart, interact])
                else:
                    # If no cart (only basket), just interact to pick up and put in basket
                    action_list.append([north, north, north, north, north, north, north, north, north, interact, interact, south, south, south, south, south, south, south, south, south])
            # If above shelf
            else:
                # Check for cart
                if has_cart:
                    # Turn left, put cart down, turn back down, move 2 down, interact, turn up, move 2 up, turn left, interact, toggle cart
                    action_list.append([west, toggle_cart, south, south, south, south, south, south, south, south, south, interact, interact, north, north, north, north, north, north, north, north, north, west, interact, toggle_cart, interact])
                else:
                    action_list.append([south, south, south, south, south, south, south, south, south, interact, interact, north, north, north, north, north, north, north, north, north])
        # Horizontal Counter
        else:
            # For fresh fish and prepared foods, agent is trained to stop at a certain corner of the counters
            if item == "prepared foods":
                # if above prepared foods
                if agent_coordinates[1] < 5.1:
                # Check for cart
                    if has_cart:
                        # If cart
                        # Turn left (to reset direction), turn right, drop off cart, turn north, move 4 up, turn right, interact, interact, turn down, move 4 down, turn right, interact, pick up cart
                        action_list.append([west, east, toggle_cart, south, south, south, south, south, south, south, south, south, south, south, east, interact, interact, interact, north, north, north, north, north, north, north, north, north, north, north, east, interact, toggle_cart, interact])
                    else:
                        # If no cart
                        action_list.append([north, north, north, north, north, north, north, north, east, interact, interact, interact, west, west, west])
                # if below prepared foods
                else: 
                # Check for cart
                    if has_cart:
                        # If cart
                        # Turn left (to reset direction), turn right, drop off cart, turn north, move 4 up, turn right, interact, interact, turn down, move 4 down, turn right, interact, pick up cart
                        action_list.append([west, east, toggle_cart, north, north, north, north, north, north, north, north, north, north, north, east, interact, interact, interact, south, south, south, south, south, south, south, south, south, south, south, east, interact, toggle_cart, interact])
                    else:
                        # If no cart
                        action_list.append([south, south, south, south, south, south, south, south, east, interact, interact, interact, west, west, west])
            if item == "fresh fish":
                # if above fresh fish
                if agent_coordinates[1] < 13.2:
                    # Check for cart
                    if has_cart:
                        # If cart
                        # Turn west (to reset direction), turn north, drop off cart, turn east, move east, interact, interact, turn west, move west, turn north, interact, pick up cart
                        action_list.append([west, north, toggle_cart, east, east, east, east, east, east, east, interact, interact, interact, west, west, west, west, west, west, west, west, north, interact, toggle_cart, interact])
                    else:
                        # If no cart
                        action_list.append([east, east, east, east, east, east, east, interact, interact, interact, west, west, west, west, ])
                else:
                    # Check for cart
                    if has_cart:
                        # If cart
                        # Turn west (to reset direction), turn north, drop off cart, turn east, move east, interact, interact, turn west, move west, turn north, interact, pick up cart
                        action_list.append([west, north, north, north, north, north, north, north, north, north, north, north, north, north, north, north, north, north, toggle_cart, east, east, east, east, east, east, east, interact, interact, interact, west, west, west, west, west, west, west, west, north, interact, toggle_cart, interact])
                    else:
                        # If no cart
                        action_list.append([north, north, north, north, north, north, north, north, north, north, north, north, north, north, north, north, north, east, east, east, east, east, east, east, interact, interact, interact, west, west, west, west, ])
    # Special Interactions (exit, carts, baskets, checkout counters)
    else:
        if item == "exit":
            action_list.append([west, west, west, west, west, west, west, west, west, west])
        if item == "carts" or item == "baskets":
            action_list.append([west, south, interact, interact, north, north])
        if item == "checkout counter":
            # The agent is trained to stop at the bottom right corner of each checkout counter.
            if has_cart:
                # With a cart, cart needs to be put directly below or above checkout counter for items to be purchased. We will put it below. 
                action_list.append([west, west, west, west, west, west, west, west, toggle_cart, north, interact, interact, interact, west, toggle_cart, south, south])
            else:
                action_list.append([west, west, west, west, west, west, west, west, north, interact, interact, interact, south, south, south])
    return action_list