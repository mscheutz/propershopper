# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import json
import socket

import pandas as pd

from final_proj.util import get_geometry
from utils import recv_socket_data


# todo: update with Helen's method for making interaction areas?
def populate_locs(observation):
    locs: dict = {}

    for idx, obj in enumerate(observation['registers']):
        locs[f'register {idx}'] = get_geometry(obj)

    for idx, obj in enumerate(observation['cartReturns']):
        locs[f'cartReturn {idx}'] = get_geometry(obj)

    for idx, obj in enumerate(observation['basketReturns']):
        locs[f'basketReturn {idx}'] = get_geometry(obj)

    for obj in observation['counters']:
        locs[obj['food']] = get_geometry(obj)

    for obj in observation['shelves']:
        locs[obj['food']] = get_geometry(obj)

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

            pass  # todo

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

    # agents = [Agent(sock_game, 0)]
    agents = [Agent(sock_game, 0), Agent(sock_game, 1), Agent(sock_game, 2)]
    while True:
        for agent in agents:
            agent.transition()
