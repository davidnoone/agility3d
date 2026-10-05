#!/bin/env python
#
# Generic serializer for python objects.
# Intended for use with "Element", but also
# will work for others... including hose in classes.py
#
#

import json
import numpy as np

#==============================================
# Classes that are allowed to be reconstructed from a file.
CLASS_REGISTRY = {}

def register_class(cls):
    """Register a class so it can be reconstructed when loading."""
    CLASS_REGISTRY[cls.__name__] = cls
    return cls

#==============================================
def serialize(obj):
    # NumPy arrays convert to list
    if isinstance(obj, np.ndarray):
        return {
            "__type__": "numpy.ndarray",
            "dtype": str(obj.dtype),
            "shape": obj.shape,
            "data": obj.tolist(),
        }

    # NumPy scalar types
    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    # Basic Python types
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Tuples
    if isinstance(obj, tuple):
        return {
            "__type__": "tuple",
            "data": [serialize(x) for x in obj],
        }

    # Lists
    if isinstance(obj, list):
        return [serialize(x) for x in obj]

    # Dictionaries
    if isinstance(obj, dict):
        return {
            key: serialize(value)
            for key, value in obj.items()
        }

    # Ordinary Python objects
    if hasattr(obj, "__dict__"):
        return {
            "__type__": type(obj).__name__,
            "data": {
                key: serialize(value)
                for key, value in obj.__dict__.items()
            },
        }

    raise TypeError(
        f"Cannot serialize object of type {type(obj).__name__}"
    )


#==============================================
def deserialize(data):

    # Primitive values
    if data is None or isinstance(data, (str, int, float, bool)):
        return data

    # Lists
    if isinstance(data, list):
        return [deserialize(x) for x in data]

    # Dictionaries
    if isinstance(data, dict):

        type_name = data.get("__type__")

        # NumPy array
        if type_name == "numpy.ndarray":
            array = np.array(
                data["data"],
                dtype=np.dtype(data["dtype"]),
            )
            return array.reshape(data["shape"])

        # Tuple
        if type_name == "tuple":
            return tuple(
                deserialize(x)
                for x in data["data"]
            )

        # Python object
        if type_name is not None:

            if type_name not in CLASS_REGISTRY:
                raise TypeError(
                    f"Unknown serialized class: {type_name}"
                )

            cls = CLASS_REGISTRY[type_name]

            # Construct without calling __init__.
            obj = cls.__new__(cls)

            for key, value in data["data"].items():
                setattr(obj, key, deserialize(value))

            return obj

        # Ordinary dictionary
        return {
            key: deserialize(value)
            for key, value in data.items()
        }

    raise TypeError(
        f"Cannot deserialize object of type {type(data).__name__}"
    )

#================================================

def save(obj, filename):
    data = serialize(obj)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump( data, f, indent=2,)

def load(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return deserialize(data)

#================================================
