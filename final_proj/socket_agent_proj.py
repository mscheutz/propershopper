
import json
import socket
import random
from copy import deepcopy

import pandas as pd
import pathfind.graph.transform

from enums.direction import Direction
from final_proj.util import get_geometry
from helper import project_collision
from util import *
from final_proj.fast_high_level_astar import *
from box_regions import *

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
    
    for idx, obj in enumerate(obs_with_boxes['carts']):
        geometry = get_geometry(obj)
        geometry['position'][1] += geometry['height'] + 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs['cart {idx}'] = geometry
    
    for idx, obj in enumerate(obs_with_boxes['baskets']):
        geometry = get_geometry(obj)
        geometry['position'][1] += geometry['height'] + 1
        geometry['interact_boxes'] = obj['interact_boxes']
        locs['basket {idx}'] = geometry

    return locs


class Agent:

    def __init__(self, conn, agent_id, env):
        self.socket = conn
        self.agent_id = agent_id
        self.env = env
        self.list_quant:list = env['observation']['players'][self.agent_id]['list_quant']
        self.shopping_list:list[tuple] = [(item, quant) for item, quant in zip(env['observation']['players'][self.agent_id]['shopping_list'], self.list_quant)]
        self.goal = ""
        self.done = False
        self.container_id = -1
        self.container_type = ''
        self.holding_container = False
        self.holding_food = None
        self.planner = HighLevelPlanner(socket_game=conn, env=env)

    def transition(self):
        self.execute(action='NOP') # this updates self.env
        if self.done:  # If we've left the store
            self.execute("NOP")  # Do nothing

        elif self.container_id == -1:  # If we don't have a container
            self.get_container()  # Get one!

        elif self.goal == "":  # If we currently don't have a goal
            if not self.shopping_list:  # Check if there's anything left on our list
                self.exit()  # Leave the store (includes checkout), might need to return basket
            else:  # We've still got something on our shopping list
                item, quantity = self.strategically_choose_from_shopping_list(self.shopping_list)
                for _ in range(quantity):
                    self.goal = item  # Set our goal to the next item on our list
                    self.get_item()  # Go to our goal
                    self.transition()
        elif self.goal == 'add_to_container':  # If we have a goal and we're here, that means we're at the goal!
            self.add_to_container()
        else: # this shouldn't happen, just exit
            self.exit()

    
    def get_item(self):
        """get `quantitiy` number of `item`

        Args:
            item (str): an item on the shopping list
        """
        print(f"Agent {self.agent_id} going to {self.goal}")
        #TODO:go to the item and get it. Look at the implementation of `get_container` for reference. target item in stored self.goal
        #change goal after getting item.
        self.holding_food = self.env['observation']['players'][self.agent_id]['holding_food']
        if self.holding_food is not None:
            self.holding_container = False #sanity check: can't hold both food and container
        if self.holding_food == self.goal:# successfully got item
            self.goal = "add_to_container"
    
    # Agent retrieves a container
    def get_container(self):
        if sum(self.list_quant) <= 6:
            self.update_container(container='basket')
            print(f"Agent {self.agent_id} getting a basket")
            if self.container_id == -1: # has never gotten a container
                self.goal = 'basketReturn 0'
                self.goto(goal='basketReturn 0', is_item=True)
            else:
                self.goal = 'basket'# we have gotten a basket before, it's somewhere in the environment
                self.goto(goal=f'basket {self.container_id}', is_item=True)
            self.execute('INTERACT')
            self.execute('INTERACT')
            self.update_container('basket')
            self.holding_container = True #we have to make this assumption, it's not reflected in the env
        else:
            print(f"Agent {self.agent_id} getting a cart")
            self.update_container(container='cart')
            if self.container_id == -1: # has never gotten a container
                self.goto(goal='cartReturn 0', is_item=True)
            else:
                self.goal = 'cart'
                self.goto(goal=f'cart {self.container_id}', is_item=True)
            self.execute('INTERACT')
            self.execute('INTERACT')
            self.update_container('cart')
        self.goal = ""

    def strategically_choose_from_shopping_list(self, shopping_list):
        """Strategically choose an item from the shopping list

        Args:
            shopping_list (list[tuple]): shopping list of (item, quantity)
        """
        #TODO: replace with optimization strategy
        return shopping_list.pop(0)
    
    def update_container(self, container='basket'):
        """Check if we are responsible for any `container` and update container related status. Either a cart or a basket

        Args:
            container (_type_): either a cart or a basket
        """
        if self.env['observation']['players'][self.agent_id]['curr_cart'] != -1:#currently holding a cart
            self.container_type = 'cart'
            self.container_id = self.env['observation']['players'][self.agent_id]['curr_cart']
            self.holding_container = True
            return
        for i, c in enumerate(self.env['observation'][container+'s']):
            if c['owner'] == self.agent_id:
                self.container_id = i
                self.container_type = container
                return
    
    
    def goto(self, goal:list|tuple|str, is_item=True):
        """go to the goal, either a (x, y) of a string such as 'basket', 'register'

        Args:
            goal (list | tuple | str): (x, y) or strings such as 'strawberry', 'basket'
            is_item (bool, optional): if the goal is an item. Set False for (x, y). Defaults to True.
        """
        if goal is None:
            goal = self.goal

        if is_item:#goal is an item in the env, not a (x, y)
            populate_locs(self.env['observation'])
            if goal in ('cartReturn 0', 'cartReturn 1', 'basketReturn 0'): # access these from the North
                interact_box = locs[goal]['interact_boxes']['NORTH_BOX']
                goal = self.interact_box_to_goal_location(box=interact_box)
            elif goal in ('cart', 'basket'):
                if self.container_type != goal:# current container and goal doesn't match, get current container instead
                    self.goto(goal=self.container_type)
                    return
                elif self.holding_container:#already holding container
                    return
                else:
                    interact_boxes:dict = locs[f'{goal} {self.container_id}']
                    if goal == 'cart':
                        interact_box = list(interact_boxes.values())[0]#cart only has one interact box, go to that interact box
                        goal= self.interact_box_to_goal_location(box=interact_box)
                    else:
                        interact_box = locs[f'{goal} {self.container_id}']['interact_boxes']['SOUTH_BOX']
                        goal= self.interact_box_to_goal_location(box=interact_box)
            else:# access everything else from the SOUTH
                interact_box = locs[goal]['interact_boxes']['SOUTH_BOX']
                goal = self.interact_box_to_goal_location(box=interact_box)

        if self.holding_container and self.container_type == 'cart':
            print(f"Agent {self.agent_id} going to location {goal} with cart")
            path = []
            pass  # TODO: goto with cart. TA says it might be as simple as changing the player's shape as long as they are holding a cart and change it back once they are not. If it's too complicated we will skip it
        else:
            print(f"Agent {self.agent_id} planning a path to {goal} without cart")
            path = self.planner.astar(
                player_id=self.agent_id,
                start=self.env['observation']['players'][self.agent_id],
                goal=goal,
                obs=self.env['observation']
            )
            print(f"Agent {self.agent_id} going to location {goal} without cart")
        
        for box_region in path:
            self.reactive_nav(goal=box_region.midpoint, is_box=False)
        
        # we should now be in the same region as the goal (x, y) location
        if is_item:
            self.reactive_nav(goal=interact_box, is_box=True)
        else:
            self.reactive_nav(goal=goal, is_box=False)

    
    def interact_box_to_goal_location(self, box:dict) -> tuple[float, float]:
        """Given an interact box, determine which goal location within the box to aim for

        Args:
            box (dict): interact box

        Returns:
            tuple[float, float]: the goal location
        """
        player_needs_to_face = box['player_needs_to_face']
        if player_needs_to_face == Direction.SOUTH:
            top_left = (box['westmost'],box['northmost'])
            return top_left
        elif player_needs_to_face == Direction.NORTH:
            bot_left = (box['westmost'],box['southmost'])
            return bot_left
        elif player_needs_to_face == Direction.WEST:
            bot_right = (box['eastmost'],box['southmost'])
            return bot_right
        else:
            bot_left = (box['westmost'],box['southmost'])
            return bot_left
    
    
    
    def reactive_nav(self, goal, is_box=False):
        """Purely reactie navigation

        Args:
            goal (_type_): (x, y) or interact_box
        """
        ##############################################
        ## The old reactive navigation code is below##
        ##############################################
        target = "x"
        reached_x = False
        reached_y = False
        stuck = 0 # stuck for timestep
        while True:
            player = self.env['observation']['players'][self.agent_id]

            if is_box:
                goal_loc = self.interact_box_to_goal_location(box=goal)
                x_dist = player['position'][0] - goal_loc['westmost']
                y_dist = player['position'][1] - goal_loc['northmost']
                if can_interact_in_box(player=player, interact_box=goal):
                    break
            else:
                x_dist = player['position'][0] - goal[0]
                y_dist = player['position'][1] - goal[1]

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
            original_command = command
            while project_collision(player, self.env, command, dist=STEP):
                command = Direction(self._turn_ninety_degrees(dir=command)) # take the 90 degrees action instead
                stuck += 1
                if stuck >= 10:#been stuck for too long, it's probably a corner, F it, take the 270 degree action
                    command = self._turn_ninety_degrees(self._turn_opposite_dir(original_command))
            if player['direction'] == command.value:
                self.execute(action=command.name)# execute once if already facing that direction
            else:
                self.execute(action=command.name)
                self.execute(action=command.name)

    def _turn_opposite_dir(self, dir:Direction) -> Direction:
        """Turn 180 degrees with respect to the given 

        Args:
            command (Direction): the direction command whose ninety degree direction we want to find
        Returns:
            returns the 90 degrees direction
        """
        if dir == Direction.NORTH:
            return Direction.SOUTH
        if dir == Direction.SOUTH:
            return Direction.NORTH
        if dir == Direction.EAST:
            return Direction.WEST
        else:
            return Direction.EAST

    def _turn_ninety_degrees(self, dir:Direction) -> Direction:
        """Turn 90 degrees clockwise with respect to the given 

        Args:
            command (Direction): the direction command whose ninety degree direction we want to find
        Returns:
            returns the 90 degrees direction
        """
        turned_dir = Direction((dir.value + 2) % 5)
        if turned_dir == Direction.NONE:
            return Direction.SOUTH
        return turned_dir

    
    
    def step(self, step_location:list|tuple, player_id:int, backtrack:list):
        """Keep locally adjusting and stepping in the right direction so that `player` ends up `close_enough` to `step_location`. `step_location` should be only one step away

        Args:
            step_location (list | tuple): a (x, y) that is assumed to be one step away from the player's current location
            player_id (int): the player id for the player that needs to be at `step_location`
            backtrack (list): a list of locations visited by the player
        """
        goal_x, goal_y = step_location
        player_x, player_y = self.env['observation']["players"][player_id]['position']
        while not self.planner.is_close_enough(current=self.env['observation']["players"][player_id]['position'], goal=step_location, tolerance=LOCATION_TOLERANCE, is_item=False):#deals with stochasticity: keep locally adjusting to the right location until it's close enough
            # compare previous position with current position to determine if a location needs to be saved in the player's backtracking trace 
            prev_x = player_x
            prev_y = player_y
            player_x, player_y = self.env['observation']["players"][player_id]['position']
            if player_x != prev_x or player_y != prev_y:#player has moved, record its prev position for potential backtracking
                backtrack.append((prev_x, prev_y))

            if manhattan_distance(self.env['observation']["players"][player_id]['position'], step_location) >= BACKTRACK_TOLERANCE:#player has wandered too far due to stochasticity, there could be an object between the player and the goal `step_location` now. The player needs to backtrack to the starting location, otherwise it could be banging its head against the object forever
                self.step(step_location=backtrack[-1], player_id=player_id, backtrack=backtrack[:-1])
                del backtrack[-1]
            elif player_x < goal_x and abs(player_x - goal_x) >= LOCATION_TOLERANCE:# player should go EAST
                #self.execute(Direction.EAST.name)
                self.reactive_nav(goal=step_location, is_box=False)
            elif player_x > goal_x and abs(player_x - goal_x) >= LOCATION_TOLERANCE:#player should go WEST
                #self.execute(Direction.WEST.name)
                self.reactive_nav(goal=step_location, is_box=False)
            elif player_y < goal_y and abs(player_y - goal_y) >= LOCATION_TOLERANCE:#player should go SOUTH
                #self.execute(Direction.SOUTH.name)
                self.reactive_nav(goal=step_location, is_box=False)
            elif player_y > goal_y and abs(player_y - goal_y) >= LOCATION_TOLERANCE:#player should go NORTH
                #self.execute(Direction.NORTH.name)
                self.reactive_nav(goal=step_location, is_box=False)
        
        # def infer_actual_action(player_state_before_execution:tuple[float, float, Direction], player_state_after_execution:tuple[float, float, Direction]):
        #     prev_x, prev_y, prev_orientation = player_state_before_execution
        #     after_x, after_y, after_orientation = player_state_after_execution
        #     if after_orientation != prev_orientation:#player turned
        #         return after_orientation
        #     elif prev_x < after_x:#player went EAST
        #         return Direction.EAST
            

    # TODO: Agent picks up an item and adds it to the cart
    def add_to_container(self):
        #self.env
        #a function to be used if the item is north of the player
        violation=self.env['violations']
        #moving the cart south of the player
        action = "0 " + "SOUTH"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        #leaving the cart
        action = "0 " + "TOGGLE_CART"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        #moving the player till it hits the shelf
        while not any("shelf" or "counter" in v for v in violation): #I've added shelf because the player might hit something else (a player of a cart)
            action = "0 " + "NORTH"
            sock_game.send(str.encode(action))  # send action to env
            output = recv_socket_data(sock_game)  # get observation from env
            self.env = json.loads(output)
            current_p_y=self.env['observation']['players'][0]['position'][1]
            violation=self.env['violations']
        #picking up the item
        action = "0 " + "INTERACT"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        #clearing the message
        action = "0 " + "INTERACT"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        action = "0 " + "WEST"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        action = "0 " + "WEST"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        action = "0 " + "WEST"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        action = "0 " + "WEST"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        violation=[]
        len(violation)
        #moving back to the cart
        while not any("basket" in v for v in violation):
            action = "0 " + "SOUTH"
            sock_game.send(str.encode(action))  # send action to env
            output = recv_socket_data(sock_game)  # get observation from env
            self.env = json.loads(output)
            current_p_y=self.env['observation']['players'][0]['position'][1]
            violation=self.env['violations']
        #placing the item to the cart
        action = "0 " + "INTERACT"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        #clearing the message
        action = "0 " + "INTERACT"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        #re-picking the cart
        action = "0 " + "TOGGLE_CART"
        sock_game.send(str.encode(action))  # send action to env
        output = recv_socket_data(sock_game)  # get observation from env
        self.env = json.loads(output)
        
        return self.env
        
        pass  # TODO

        self.goal = ""

    # TODO use other functions to complete checkout
    def exit(self):
        print(f"Agent {self.agent_id} exiting")
        self.goto(goal='register 0', is_item=True)

        
        self.goto([-0.6, 3.0], is_item=False)#upper exit

        self.done = True

    # Reads the shopping list
    def init_list(self):
        print(f"Agent {self.agent_id} reading list")
        shopping_list = []
        self.execute("NOP")
        shopping_list += self.env['observation']["players"][self.agent_id]["shopping_list"].copy()
        return shopping_list

    # Given an action, executes it for this agent
    def execute(self, action):
        action = f"{self.agent_id} {action}"
        self.socket.send(str.encode(action))  # send action to env
        output = recv_socket_data(self.socket)  # get observation from env
        self.env = json.loads(output)


if __name__ == "__main__":

    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']

    print("action_commands: ", action_commands)

    # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))
    sock_game.send(str.encode("0 RESET"))  # reset the game
    state = recv_socket_data(sock_game)
    sock_game.send(str.encode("0 NOP"))  # send action to env
    output = recv_socket_data(sock_game)  # get observation from env
    output = json.loads(output)
    locs = populate_locs(output['observation'])
    agents = [Agent(sock_game, 0, env=output)]
    # agents = [Agent(sock_game, 0), Agent(sock_game, 1), Agent(sock_game, 2)]
    while True:
        for agent in agents:
            agent.transition()
