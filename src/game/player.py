from .state import RenderObject, Transform


class Player:
    def __init__(self, object_id):
        self.id = object_id

        self.geometry = "cube"

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.rx = 0.0
        self.ry = 0.0
        self.rz = 0.0

        self.spin_speed = 1.0

    def update(self, dt):
        self.ry += self.spin_speed * dt


