#!/bin/env python
#
# TOP LEVEL GAME
# Run from the command line to see world creation summary.
#
#

from .physics import Physics
from .creation import create_world

class Game:
    def __init__(self):

        # Set parameters (get this from yaml later, and pass in)
        params = {
            "field": {
                "length": 30_000,
                "width": 40_000,
            },

            "table": {
                "height": 900,
                "length": 800,
                "width": 800,
                "leg_thick": 50,
                "top_thick": 30,
            },
        }

        self.world = create_world(params)
        self.physics = Physics()

    def update(self, dt):
        self.physics.update(self.world, dt)
        #self.world.update(dt)

    def render_state(self):
        """ Returns a list of all objects that canbe passed to the renderer"""
        objects = []

        for object_id, (element, transform) in enumerate(self.world.walk()):
            if element.geometry is None:
                continue

            geometry = element.geometry

            objects.append((
                object_id,
                {
                    "points": geometry.points.tolist(),
                    "faces": [
                        face.tolist()
                        for face in geometry.faces
                    ],
                },
                transform.tolist(),
                {
                    "face_color": element.style.face_color,
                    "edge_color": element.style.edge_color,
                    "edge_width": element.style.edge_width,
                    "alpha":      element.style.alpha,
                    "visible":    element.style.visible,
                    "show_edges": element.style.show_edges,
                },
            ))

        return objects


if __name__ == "__main__":
    print("COMMAND LINE TEST EXECUTION")
    game = Game()

    # Check what we have created
    game.world.print_tree()