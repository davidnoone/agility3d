from .player import Player


class World:
    def __init__(self):
        self.objects = {}

        # Create the game objects.
        self.player = Player(object_id=1)
        self.add_object(self.player)

    def add_object(self, obj):
        self.objects[obj.id] = obj

    def remove_object(self, obj_id):
        del self.objects[obj_id]

    def update(self, dt):
        for obj in self.objects.values():
            obj.update(dt)

    def render_state(self):
        """
        Return a compact representation intended to cross
        the Python -> JavaScript boundary.

        Each object is:

            (id, geometry, px, py, pz, rx, ry, rz)
        """

        return [
            (
                obj.id,
                obj.geometry,
                obj.x,
                obj.y,
                obj.z,
                obj.rx,
                obj.ry,
                obj.rz,
            )
            for obj in self.objects.values()
        ]