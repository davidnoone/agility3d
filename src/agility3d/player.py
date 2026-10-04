from .state import RenderObject, Transform


class Player:

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.rx = 0.0
        self.ry = 0.0
        self.rz = 0.0

        self.spin_speed = 1.0

    def update(self, dt):
        self.ry += self.spin_speed * dt

    def render_object(self):
        return RenderObject(
            name="player",
            transform=Transform(
                position=(self.x, self.y, self.z),
                rotation=(self.rx, self.ry, self.rz),
            ),
        )