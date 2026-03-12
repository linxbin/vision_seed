import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.simultaneous.eye_find_patterns.services import EyeFindPatternService, EyeFindSessionService


class EyeFindServicesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_pattern_service_builds_surface_and_positions(self):
        service = EyeFindPatternService()
        pattern = service.next_pattern(size=140)
        self.assertIn(pattern["pattern_id"], service.PATTERN_IDS)
        self.assertEqual(pattern["surface"].get_size(), (140, 140))
        left, right = service.reset_positions(900, 700)
        self.assertNotEqual(left, right)
        self.assertGreaterEqual(len(service.PATTERN_IDS), 12)
        self.assertIn("leaf", service.PATTERN_IDS)
        self.assertIn("flower", service.PATTERN_IDS)
        self.assertIn("kite", service.PATTERN_IDS)
        self.assertIn("mushroom", service.PATTERN_IDS)

    def test_new_pattern_types_render_non_empty_fallbacks(self):
        service = EyeFindPatternService()
        color = (255, 214, 140, 255)
        for pattern_id in ("leaf", "flower", "apple", "kite", "crown", "shell", "heart", "mushroom"):
            surface = service.build_pattern_surface(pattern_id, 140, color)
            alpha = pygame.surfarray.array_alpha(surface)
            self.assertGreater(int(alpha.max()), 0, msg=pattern_id)

    def test_session_service_tracks_attempt_and_session(self):
        service = EyeFindSessionService(300, 30)
        service.start(now=10.0)
        session_elapsed, attempt_elapsed = service.tick(now=25.0)
        self.assertEqual(session_elapsed, 15.0)
        self.assertEqual(attempt_elapsed, 15.0)
        self.assertFalse(service.is_attempt_timed_out())
        service.tick(now=45.0)
        self.assertTrue(service.is_attempt_timed_out())
        service.restart_attempt(now=50.0)
        self.assertEqual(service.attempt_elapsed, 0.0)

    def test_pattern_filter_only_applies_in_glasses_mode(self):
        service = EyeFindPatternService()
        base = pygame.Surface((8, 8), pygame.SRCALPHA)
        base.fill((0, 0, 0, 0))
        pygame.draw.circle(base, (100, 100, 100, 255), (4, 4), 2)
        naked = service.apply_filter(base, "naked", "left_red_right_blue", "left", "glasses", "left_red_right_blue")
        self.assertEqual(naked.get_at((0, 0)), base.get_at((0, 0)))
        filtered = service.apply_filter(base, "glasses", "left_red_right_blue", "left", "glasses", "left_red_right_blue")
        self.assertNotEqual(filtered.get_at((0, 0)), base.get_at((0, 0)))
        self.assertEqual(filtered.get_at((0, 0))[3], 0)
        self.assertEqual(filtered.get_at((4, 4))[:3], (255, 0, 0))
        self.assertEqual(filtered.get_at((4, 4))[3], 255)
        self.assertEqual(service.GLASSES_BACKGROUND, (255, 19, 255, 179))
        self.assertEqual(service.RED_FILTER, (255, 0, 0, 255))
        self.assertEqual(service.BLUE_FILTER, (0, 0, 255, 255))

    def test_overlapped_red_and_blue_patterns_blend_instead_of_cover(self):
        service = EyeFindPatternService()
        base = pygame.Surface((8, 8), pygame.SRCALPHA)
        base.fill((0, 0, 0, 0))
        pygame.draw.circle(base, (255, 255, 255, 255), (4, 4), 2)
        red = service.apply_filter(base, "glasses", "left_red_right_blue", "left", "glasses", "left_red_right_blue")
        blue = service.apply_filter(base, "glasses", "left_red_right_blue", "right", "glasses", "left_red_right_blue")
        merged = service.blend_filtered_patterns((8, 8), red, red.get_rect(), blue, blue.get_rect())
        pixel = merged.get_at((4, 4))
        self.assertNotEqual(pixel[:3], (255, 12, 6))
        self.assertNotEqual(pixel[:3], (0, 9, 255))
        self.assertLess(pixel[0], 32)
        self.assertLess(pixel[2], 32)
        self.assertGreater(pixel[3], 0)


if __name__ == "__main__":
    unittest.main()
