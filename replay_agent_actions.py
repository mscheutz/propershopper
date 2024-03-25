# Author: Tia Chen
# Email: qingyan.chen@tufts.edu

import argparse
import json
import socket

from utils import recv_socket_data


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        'filename',
        type=str, 
        help="provide a file name containing playey action records to replay",
    )
    args = parser.parse_args()
    
    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']
    print("action_commands: ", action_commands) 

    # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))

    actions = []
    with open(args.filename, "r") as file:
        for line in file:
            columns = line.strip().split(' ')
            actions.append(columns[0] + ' ' + columns[1])
        
    for action in actions:
        print("Sending action: ", action)
        sock_game.send(str.encode(action))  # send action to env

        output = recv_socket_data(sock_game)  # get observation from env
        output = json.loads(output)

        print("JSON: ", output)
