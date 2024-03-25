# Author: Tia Chen
# Email: qingyan.chen@tufts.edu

import argparse
import json
import socket
import pygame

from utils import recv_socket_data

def send_command(command):
    print("Sending action: ", command)
    sock_game.send(str.encode(command))  # send action to env

    output = recv_socket_data(sock_game)  # get observation from env (wait for response before sending next command)
    # output = json.loads(output) # Put back if you want to inspect received message

    # print("JSON: ", output)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        'player_id',
        type=int, 
        help="Please provide the player id that you are playing for",
    )
    args = parser.parse_args()
    
    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT', 'CANCEL']
    
    game_commands = ['ESCAPE', 'SAVE', 'TOGGLE_RECORD', 'PAUSE', 'REVERT']
    
    print("action_commands: ", action_commands) 
    print("game_commands: ", game_commands)

    # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))

    pygame.init()

    # Set up a display to accept keyboard command
    screen_size = (400, 100)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Control Display")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # game events
                if event.key == pygame.K_ESCAPE:
                    send_command('ESCAPE')
                elif event.key == pygame.K_s:
                    send_command('SAVE')
                elif event.key == pygame.K_r:
                    send_command('TOGGLE_RECORD')
                elif event.key == pygame.K_p:
                    send_command('PAUSE')
                elif event.key == pygame.K_z:
                    send_command('REVERT')
                elif event.key == pygame.K_c:
                    send_command(str(args.player_id) + ' TOGGLE_CART')
                elif event.key == pygame.K_RETURN:
                    send_command(str(args.player_id) + ' INTERACT')
                elif event.key == pygame.K_b:
                    send_command(str(args.player_id) + ' CANCEL')


        # Player events to send repeatedly to smooth transition
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            send_command(str(args.player_id) + ' NORTH')
        elif keys[pygame.K_DOWN]:
            send_command(str(args.player_id) + ' SOUTH')
        elif keys[pygame.K_LEFT]:
            send_command(str(args.player_id) + ' WEST')
        elif keys[pygame.K_RIGHT]:
            send_command(str(args.player_id) + ' EAST')
            
    pygame.quit()
    exit()