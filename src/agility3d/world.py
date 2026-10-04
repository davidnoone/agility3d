from .player import Player


class World:

    def __init__(self):
        self.player = Player()

    def update(self, dt):
        self.player.update(dt)

    def render_objects(self):
        return [
            self.player.render_object()
        ]