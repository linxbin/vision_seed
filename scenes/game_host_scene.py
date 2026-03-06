from core.base_scene import BaseScene


class GameHostScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.active_game_scene = None
        self.active_game_id = None

    def _mount_if_needed(self):
        game_id = self.manager.active_game_id
        if not game_id:
            self.active_game_scene = None
            self.active_game_id = None
            return

        if self.active_game_scene is not None and game_id == self.active_game_id:
            return

        game = self.manager.game_registry.get_game(game_id)
        if not game:
            self.active_game_scene = None
            self.active_game_id = None
            return

        self.active_game_scene = game.factory(self.manager)
        self.active_game_id = game_id
        if self.manager.screen_size and hasattr(self.active_game_scene, "on_resize"):
            self.active_game_scene.on_resize(*self.manager.screen_size)
        reset = getattr(self.active_game_scene, "reset", None)
        if callable(reset):
            reset()

    def on_enter(self):
        self._mount_if_needed()

    def on_resize(self, width, height):
        if self.active_game_scene:
            self.active_game_scene.on_resize(width, height)

    def handle_events(self, events):
        self._mount_if_needed()
        if self.active_game_scene:
            self.active_game_scene.handle_events(events)
        else:
            self.manager.set_scene("category")

    def update(self):
        self._mount_if_needed()
        if self.active_game_scene:
            self.active_game_scene.update()

    def draw(self, screen):
        self._mount_if_needed()
        if self.active_game_scene:
            self.active_game_scene.draw(screen)
        else:
            screen.fill((10, 14, 22))
