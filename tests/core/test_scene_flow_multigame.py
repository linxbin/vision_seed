import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.game_contract import GameDescriptor
from scenes.category_scene import CategoryScene
from scenes.game_host_scene import GameHostScene
from scenes.menu_scene import MenuScene


class _FakeGameRegistry:
    def __init__(self, descriptor):
        self._descriptor = descriptor

    def get_categories(self):
        return [{"id": "accommodation", "name": "调节训练"}]

    def get_games_by_category(self, category_id):
        if category_id == "accommodation":
            return [self._descriptor]
        return []

    def get_game(self, game_id):
        if game_id == self._descriptor.game_id:
            return self._descriptor
        return None


class _FlowManagerStub:
    def __init__(self, registry):
        self.settings = {"language": "en-US"}
        self.game_registry = registry
        self.active_category = None
        self.active_game_id = None
        self.screen_size = (900, 700)
        self.last_scene = None

    def t(self, key, **_kwargs):
        return key

    def set_scene(self, name):
        self.last_scene = name


class _DummyGameScene:
    def __init__(self, manager):
        self.manager = manager
        self.reset_calls = 0
        self.resize_calls = 0
        self.handle_calls = 0
        self.update_calls = 0
        self.draw_calls = 0

    def reset(self):
        self.reset_calls += 1

    def on_resize(self, _w, _h):
        self.resize_calls += 1

    def handle_events(self, events):
        self.handle_calls += 1
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.manager.set_scene("report")

    def update(self):
        self.update_calls += 1

    def draw(self, _screen):
        self.draw_calls += 1


class SceneFlowMultiGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_menu_to_category_to_game_host_flow(self):
        descriptor = GameDescriptor(
            game_id="accommodation.fake",
            category="accommodation",
            name="Fake Game",
            factory=lambda manager: _DummyGameScene(manager),
        )
        manager = _FlowManagerStub(_FakeGameRegistry(descriptor))

        menu = MenuScene(manager)
        menu.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(manager.last_scene, "category")
        self.assertEqual(manager.active_category, "accommodation")

        category = CategoryScene(manager)
        category.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(manager.last_scene, "game_host")
        self.assertEqual(manager.active_game_id, "accommodation.fake")

        host = GameHostScene(manager)
        host.on_enter()
        self.assertIsNotNone(host.active_game_scene)
        self.assertEqual(host.active_game_scene.reset_calls, 1)
        self.assertEqual(host.active_game_scene.resize_calls, 1)

        surface = pygame.Surface((900, 700))
        host.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        host.update()
        host.draw(surface)
        self.assertEqual(manager.last_scene, "report")
        self.assertEqual(host.active_game_scene.handle_calls, 1)
        self.assertEqual(host.active_game_scene.update_calls, 1)
        self.assertEqual(host.active_game_scene.draw_calls, 1)


if __name__ == "__main__":
    unittest.main()
