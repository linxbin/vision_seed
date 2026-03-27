import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.asset_loader import load_image_if_exists, project_path


class AssetLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_loads_eye_find_pattern_asset(self):
        path = project_path("games", "simultaneous", "eye_find_patterns", "assets", "objects", "star.png")
        image = load_image_if_exists(path, (64, 64))
        self.assertIsNotNone(image)
        self.assertEqual(image.get_size(), (64, 64))

    def test_loads_catch_fruit_asset(self):
        path = project_path("games", "accommodation", "catch_fruit", "assets", "objects", "apple.png")
        image = load_image_if_exists(path, (72, 72))
        self.assertIsNotNone(image)
        self.assertEqual(image.get_size(), (72, 72))


if __name__ == "__main__":
    unittest.main()
