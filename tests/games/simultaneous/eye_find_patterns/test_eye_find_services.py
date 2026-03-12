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
        self.assertIn("fish", service.PATTERN_IDS)
        self.assertIn("rocket", service.PATTERN_IDS)

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
        base.fill((100, 100, 100, 255))
        naked = service.apply_filter(base, "naked", "left_red_right_blue", "left", "glasses", "left_red_right_blue")
        self.assertEqual(naked.get_at((0, 0)), base.get_at((0, 0)))
        filtered = service.apply_filter(base, "glasses", "left_red_right_blue", "left", "glasses", "left_red_right_blue")
        self.assertNotEqual(filtered.get_at((0, 0)), base.get_at((0, 0)))


if __name__ == "__main__":
    unittest.main()
