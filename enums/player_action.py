from enum import IntEnum

class PlayerAction(IntEnum):
    NOP         = 0,
    NORTH       = 1,
    SOUTH       = 2,
    EAST        = 3,
    WEST        = 4,
    INTERACT    = 5,
    TOGGLE_CART = 6,
    CANCEL      = 7,
    PICKUP      = 8,
    RESET       = 9

    @classmethod
    def get_names(cls):
        return [member.name for member in cls]
