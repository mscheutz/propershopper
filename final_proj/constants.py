###########################Helen: ################################################
##some constants that were useful during single agent norm-conforming navigation##
##################################################################################
exit_pos = [-0.6, 3.0]
default_start_pos = [1.5, 15.6]
interact_distance = 0.25
cart_pos_left = [1, 18.5] # The position of the cart in the environment from [1, 2] in x, and y = 18.5
cart_pos_right = [2, 18.5]
basketReturn = []
counter = []
loc = [1, 17.5]
register_region_x = 1 + 2.25
vertical_walkway_west_x = 4.2
vertical_walkway_east_x = 17.1 # if east of this, walk west past it first
west_east_walkway_y = 15
west_region_x = 5.5
east_region_x = 15.5
isle_1 = [3.8, 3.2]
isle_2 = []
player_directions = {0:"NORTH", 1:"SOUTH", 2:"EAST", 3:"WEST"} # direction the player is facing
left_cartReturns = {
            "height": 6,
            "width": 0.7,
            "position": [
                1,
                18.5
            ],
            "quantity": 5,
            "interact_boxes": [
                {
                    "northmost": 18.15,
                    "westmost": 1,
                    "southmost": 18.5,
                    "eastmost": 1.7,
                    "player_needs_to_face": "SOUTH"
                }
            ]
        }