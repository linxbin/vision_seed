import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.common.anaglyph import FILTER_LR, SUBTRACTIVE_BACKGROUND, apply_filter, blend_filtered_patterns


class AnaglyphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_subtractive_blend_keeps_red_blue_and_overlap_black(self):
        left = pygame.Surface((40, 40), pygame.SRCALPHA)
        right = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(left, (255, 255, 255, 255), pygame.Rect(8, 10, 14, 18))
        pygame.draw.rect(right, (255, 255, 255, 255), pygame.Rect(16, 10, 14, 18))

        left_filtered = apply_filter(left, "glasses", FILTER_LR, "left")
        right_filtered = apply_filter(right, "glasses", FILTER_LR, "right")
        blended = blend_filtered_patterns((40, 40), left_filtered, (0, 0), right_filtered, (0, 0))

        canvas = pygame.Surface((40, 40))
        canvas.fill(SUBTRACTIVE_BACKGROUND[:3])
        canvas.blit(blended, (0, 0))

        self.assertEqual(canvas.get_at((12, 18))[:3], (255, 0, 0))
        self.assertEqual(canvas.get_at((26, 18))[:3], (0, 0, 255))
        self.assertEqual(canvas.get_at((18, 18))[:3], (0, 0, 0))
        self.assertEqual(canvas.get_at((2, 2))[:3], SUBTRACTIVE_BACKGROUND[:3])

    def test_crop_border_clears_shifted_edge_artifacts(self):
        left = pygame.Surface((24, 24), pygame.SRCALPHA)
        right = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(left, (255, 255, 255, 255), pygame.Rect(0, 4, 20, 16))
        pygame.draw.rect(right, (255, 255, 255, 255), pygame.Rect(4, 4, 20, 16))

        left_filtered = apply_filter(left, "glasses", FILTER_LR, "left")
        right_filtered = apply_filter(right, "glasses", FILTER_LR, "right")
        blended = blend_filtered_patterns((24, 24), left_filtered, (0, 0), right_filtered, (0, 0), crop_border=3)

        canvas = pygame.Surface((24, 24))
        canvas.fill(SUBTRACTIVE_BACKGROUND[:3])
        canvas.blit(blended, (0, 0))

        self.assertEqual(canvas.get_at((1, 12))[:3], SUBTRACTIVE_BACKGROUND[:3])
        self.assertEqual(canvas.get_at((22, 12))[:3], SUBTRACTIVE_BACKGROUND[:3])
        self.assertNotEqual(canvas.get_at((12, 12))[:3], SUBTRACTIVE_BACKGROUND[:3])
