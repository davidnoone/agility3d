#!/bin/env python
#
# TOP LEVEL GAME
# Run from the command line to see world creation summary.
#
#
from .physics import Physics
from .classes import BehaviourMotion
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
        self.behaviours = []

        self.player = self.world.find('player')     # pointer to player
        self.player_motion = BehaviourMotion(self.player)

        self.behaviours.append(self.player_motion)
        self.physics = Physics()        # "nop" (doesn't do anything)

    def update(self, dt):
        # Called once per frame
        self.physics.update(self.world, dt)

        for behaviour in self.behaviours:
            behaviour.update(dt)


    def set_input( self, key_left=False, key_right=False, 
                    key_forward=False,  key_backward=False): 

        # Change player speed based on key state (better in Behaviour?)
        speed = 2000.0       # mm/s
        turn_speed = 90.0    # degrees/s

        self.player_motion.u = 0.0
        self.player_motion.v = 0.0
        self.player_motion.omega_z = 0.0

        if key_forward:
            self.player_motion.v += speed           # Or "v". define, N or W as forward?
        if key_backward:
            self.player_motion.v -= speed
        if key_left:
            self.player_motion.omega_z += turn_speed
        if key_right:
            self.player_motion.omega_z -= turn_speed


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


#=======================================================
if __name__ == "__main__":
    print("COMMAND LINE TEST EXECUTION")
    game = Game()

    # Check what we have created
    game.world.print_tree()