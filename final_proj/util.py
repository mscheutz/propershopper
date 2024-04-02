from copy import deepcopy


def get_geometry(obj):
    obj_copy = deepcopy(obj)
    return {
        "position": obj_copy["position"],
        "height": obj_copy["height"],
        "width": obj_copy["width"]
    }
