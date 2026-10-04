from .world import World
from .physics import Physics


class Game:

    def __init__(self):
        self.world = World()
        self.physics = Physics()

    def update(self, dt):
        self.physics.update(self.world, dt)
        self.world.update(dt)

    def render_state(self):
        return self.world.render_state()