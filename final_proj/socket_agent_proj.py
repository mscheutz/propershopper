# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import json
import socket
from copy import deepcopy

import pandas as pd
import pathfind.graph.transform

from enums.direction import Direction
from final_proj.util import get_geometry
from helper import project_collision
from util import *


STEP = 0.15

# todo: update with Helen's method for making interaction areas?
def populate_locs(observation):
    # add interaction areas to objects in the observation
    obs_with_boxes = add_interact_boxes_to_obs(obs=observation)
    locs: dict = {}

    for idx, obj in enumerate(obs_with_boxes['registers']):
        geometry = get_geometry(obj)
        geometry['position'][0] += geometry['width'] + 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs[f'register {idx}'] = geometry

    for idx, obj in enumerate(obs_with_boxes['cartReturns']):
        geometry = get_geometry(obj)
        geometry['position'][1] -= 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs[f'cartReturn {idx}'] = geometry

    for idx, obj in enumerate(obs_with_boxes['basketReturns']):
        geometry = get_geometry(obj)
        geometry['position'][1] -= 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs[f'basketReturn {idx}'] = geometry

    for obj in obs_with_boxes['counters']:
        geometry = get_geometry(obj)
        geometry['position'][0] -= 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs[obj['food']] = geometry

    for obj in obs_with_boxes['shelves']:
        geometry = get_geometry(obj)
        geometry['position'][1] += geometry['height'] + 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs[obj['food']] = geometry

    return locs


class Agent:

    def __init__(self, conn, agent_id):
        self.socket = conn
        self.agent_id = agent_id
        self.obs = None
        self.shopping_list: list = self.init_list()
        self.goal = ""
        self.done = False
        self.has_cart = False

    def transition(self):
        if self.done:  # If we've left the store
            self.execute("NOP")  # Do nothing

        elif not self.has_cart:  # If we don't have a cart
            self.get_cart()  # Get one!

        elif self.goal == "":  # If we currently don't have a goal
            if not self.shopping_list:  # Check if there's anything left on our list
                self.exit()  # Leave the store (includes checkout)
            else:  # We've still got something on our shopping list
                item = self.shopping_list.pop(0)
                self.goal = locs[item]  # Set our goal to the next item on our list
                self.goto()  # Go to our goal

        else:  # If we have a goal and we're here, that means we're at the goal!
            self.add_to_cart()

    # Agent retrieves a
    def get_cart(self):
        print(f"Agent {self.agent_id} getting a cart/basket")

        pass  # todo

        self.has_cart = True

    def goto(self, goal=None):
        if goal is None:
            goal = self.goal

        # todo: check if we're holding a cart
        holding_cart = False
        if holding_cart:
            print(f"Agent {self.agent_id} going to location {goal} with cart")

            pass  # todo
        else:
            print(f"Agent {self.agent_id} going to location {goal} without cart")
            self.nav(goal)

    def nav(self, goal):
        target = "x"
        reached_x = False
        reached_y = False
        while True:
            player = self.obs['observation']['players'][self.agent_id]

            x_dist = player['position'][0] - goal['position'][0]
            y_dist = player['position'][1] - goal['position'][1]

            if abs(x_dist) < STEP:
                reached_x = True
            if abs(y_dist) < STEP:
                reached_y = True
            if reached_x and reached_y:
                break

            if target == "x":
                if x_dist < -STEP:
                    command = Direction.EAST
                elif x_dist > STEP:
                    command = Direction.WEST
                else:
                    reached_y = False
                    target = "y"
                    continue
            else:
                if y_dist < -STEP:
                    command = Direction.SOUTH
                elif y_dist > STEP:
                    command = Direction.NORTH
                else:
                    reached_x = False
                    target = "x"
                    continue

            while project_collision(player, self.obs, command, 0.8):
                command = Direction((command.value + 1) % 4)
            self.step(command, player)

    def step(self, command: Direction, player):
        if not command == player['direction']:
            self.execute(command.name)
        self.execute(command.name)

    # Agent picks up an item and adds it to the cart
    def add_to_cart(self):
        print(f"Agent {self.agent_id} adding an item to the cart")

        pass  # todo

        self.goal = ""

    # todo
    def exit(self):
        print(f"Agent {self.agent_id} exiting")

        pass  # todo

        self.done = True

    # Reads the shopping list
    def init_list(self):
        print(f"Agent {self.agent_id} reading list")
        shopping_list = []
        self.execute("NOP")
        shopping_list += self.obs['observation']["players"][self.agent_id]["shopping_list"].copy()
        return shopping_list

    # Given an action, executes it for this agent
    def execute(self, action):
        action = f"{self.agent_id} {action}"
        self.socket.send(str.encode(action))  # send action to env
        output = recv_socket_data(self.socket)  # get observation from env
        self.obs = json.loads(output)


if __name__ == "__main__":

    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']

    print("action_commands: ", action_commands)

    # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))

    sock_game.send(str.encode("0 NOP"))  # send action to env
    output = recv_socket_data(sock_game)  # get observation from env
    output = json.loads(output)
    locs = populate_locs(output['observation'])
    agents = [Agent(sock_game, 0)]
    # agents = [Agent(sock_game, 0), Agent(sock_game, 1), Agent(sock_game, 2)]
    while True:
        for agent in agents:
            agent.transition()
