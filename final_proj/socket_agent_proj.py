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
from final_proj.astar_path_planner import *


STEP = 0.15 # the size of the player's step

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

    def __init__(self, conn, agent_id, env):
        self.socket = conn
        self.agent_id = agent_id
        self.obs = env['observation']
        self.shopping_list: list = self.init_list()
        self.goal = ""
        self.done = False
        self.has_cart = False
        self.astar_planner = Astar_agent(socket_game=conn, env=env)

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

        # always grabs a basket for now
        self.goto(basketReturns, is_item=True)

        self.has_cart = True

    def check_has_container(self, container):
        """Check if we have are holding the `container`. Either a cart or a basket

        Args:
            container (_type_): either a cart or a basket
        """
        #TODO:Helen implement this
    
    def goto(self, goal=None, is_item=True):
        if goal is None:
            goal = self.goal

        # todo: check if we're holding a cart
        holding_cart = False
        if holding_cart:
            print(f"Agent {self.agent_id} going to location {goal} with cart")

            pass  # TODO: goto with cart. TA says it might be as simple as changing the player's shape. If it's too complicated we will skip it
        else:
            print(f"Agent {self.agent_id} planning a path to {goal} without cart")
            path = self.nav(goal, is_item=is_item)
            print(f"Agent {self.agent_id} going to location {goal} without cart")
        
        for intermediate_target_location in path:
            player = self.obs['observation']['players'][self.agent_id]
            self.step(step_location=intermediate_target_location, player=player, backtrack=[])

    def nav(self, goal, is_item=True):
        player = self.obs['observation']['players'][self.agent_id]
        player_location = player['position']
        path = self.astar_planner.astar(start=player_location, goal=goal, map_width=MAP_WIDTH, map_height=MAP_HEIGHT, objs=objs, is_item=is_item)
        return path # this returns a path of x, y locations that the agent will go through
        #####################################
        ## The old navigation code is below##
        #####################################
        # target = "x"
        # reached_x = False
        # reached_y = False
        # while True:
        #     player = self.obs['observation']['players'][self.agent_id]

        #     x_dist = player['position'][0] - goal['position'][0]
        #     y_dist = player['position'][1] - goal['position'][1]

        #     if abs(x_dist) < STEP:
        #         reached_x = True
        #     if abs(y_dist) < STEP:
        #         reached_y = True
        #     if reached_x and reached_y:
        #         break

        #     if target == "x":
        #         if x_dist < -STEP:
        #             command = Direction.EAST
        #         elif x_dist > STEP:
        #             command = Direction.WEST
        #         else:
        #             reached_y = False
        #             target = "y"
        #             continue
        #     else:
        #         if y_dist < -STEP:
        #             command = Direction.SOUTH
        #         elif y_dist > STEP:
        #             command = Direction.NORTH
        #         else:
        #             reached_x = False
        #             target = "x"
        #             continue

        #     while project_collision(player, self.obs, command, 0.8):
        #         command = Direction((command.value + 1) % 4)
        #     self.step(command, player)

    def step(self, step_location:list|tuple, player, backtrack:list):
        """Keep locally adjusting and stepping in the right direction so that `player` ends up `close_enough` to `step_location`. `step_location` should be only one step away

        Args:
            step_location (list | tuple): a (x, y) that is assumed to be one step away from the player's current location
            player (_type_): the player object that needs to be at `step_location`
            backtrack (list): a list of locations visited by the player
        """
        goal_x, goal_y = step_location
        player_x, player_y = player['position']
        while not self.astar_planner.is_close_enough(current=player['position'], goal=step_location, tolerance=LOCATION_TOLERANCE, is_item=False):#deals with stochasticity: keep locally adjusting to the right location until it's close enough
            # compare previous position with current position to determine if a location needs to be saved in the player's backtracking trace 
            prev_x = player_x
            prev_y = player_y
            player_x, player_y = player['position']
            if player_x != prev_x or player_y != prev_y:#player has moved, record its prev position for potential backtracking
                backtrack.append((prev_x, prev_y))

            if manhattan_distance(player['position'], step_location) >= BACKTRACK_TOLERANCE:#player has wandered too far due to stochasticity, there could be an object between the player and the goal `step_location` now. The player needs to backtrack to the starting location, otherwise it could be banging its head against the object forever
                self.step(step_location=backtrack[-1], player=player, backtrack=backtrack[:-1])
                del backtrack[-1]
            elif player_x < goal_x and abs(player_x - goal_x) >= LOCATION_TOLERANCE:# player should go EAST
                self.execute(Direction.EAST.name)
            elif player_x > goal_x and abs(player_x - goal_x) >= LOCATION_TOLERANCE:#player should go WEST
                self.execute(Direction.WEST.name)
            elif player_y < goal_y and abs(player_y - goal_y) >= LOCATION_TOLERANCE:#player should go SOUTH
                self.execute(Direction.SOUTH.name)
            elif player_y < goal_y and abs(player_y - goal_y) >= LOCATION_TOLERANCE:#player should go NORTH
                self.execute(Direction.NORTH.name)
        
        # def infer_actual_action(player_state_before_execution:tuple[float, float, Direction], player_state_after_execution:tuple[float, float, Direction]):
        #     prev_x, prev_y, prev_orientation = player_state_before_execution
        #     after_x, after_y, after_orientation = player_state_after_execution
        #     if after_orientation != prev_orientation:#player turned
        #         return after_orientation
        #     elif prev_x < after_x:#player went EAST
        #         return Direction.EAST
            

    # TODO: Agent picks up an item and adds it to the cart
    def add_to_cart(self):
        print(f"Agent {self.agent_id} adding an item to the cart")

        pass  # todo

        self.goal = ""

    # TODO use other functions to complete checkout
    def exit(self):
        print(f"Agent {self.agent_id} exiting")
        self.goto([2, 12.5])

        # pick_up_and_put_in(shelf_direction = "NORTH")
        # self.add_to_cart()
        
        self.goto([-0.8, 15.6])

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
    agents = [Agent(sock_game, 0, env=output)]
    # agents = [Agent(sock_game, 0), Agent(sock_game, 1), Agent(sock_game, 2)]
    while True:
        for agent in agents:
            agent.transition()
