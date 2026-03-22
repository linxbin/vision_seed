import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.accommodation.snake.scenes.root_scene import SnakeFocusScene
from games.amblyopia.fruit_slice.scenes.root_scene import FruitSliceScene
from games.amblyopia.whack_a_mole.scenes.root_scene import WhackAMoleScene
from games.fusion.path_fusion.scenes.root_scene import PathFusionScene
from games.fusion.tetris.scenes.root_scene import FusionTetrisScene
from games.stereopsis.ring_flight.scenes.root_scene import RingFlightScene
from games.suppression.find_same.scenes.root_scene import FindSameScene
from games.suppression.red_blue_catch.scenes.root_scene import RedBlueCatchScene


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.screen_size = (1600, 900)
        self.data_manager = None
        self.sound_manager = None

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, _name):
        pass


class NewGameResizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_new_games_follow_screen_resize(self):
        scene_types = (
            SnakeFocusScene,
            FindSameScene,
            RedBlueCatchScene,
            RingFlightScene,
            WhackAMoleScene,
            FruitSliceScene,
            FusionTetrisScene,
            PathFusionScene,
        )
        for scene_type in scene_types:
            with self.subTest(scene=scene_type.__name__):
                scene = scene_type(_ManagerStub())
                scene.on_resize(1600, 900)
                self.assertEqual(scene.width, 1600)
                self.assertEqual(scene.height, 900)

    def test_find_same_reset_preserves_screen_size(self):
        manager = _ManagerStub()
        scene = FindSameScene(manager)
        scene.on_resize(1600, 900)
        scene.reset()
        self.assertEqual(scene.width, 1600)
        self.assertEqual(scene.height, 900)


if __name__ == "__main__":
    unittest.main()
