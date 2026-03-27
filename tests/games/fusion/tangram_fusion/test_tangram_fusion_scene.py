import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.fusion.tangram_fusion.scenes.root_scene import TangramFusionScene
from games.common.anaglyph import GLASSES_BACKGROUND


class _DataManagerStub:
    def __init__(self):
        self.saved = []

    def save_training_session(self, payload):
        self.saved.append(payload)
        return True


class _SoundManagerStub:
    def __init__(self):
        self.correct_calls = 0
        self.wrong_calls = 0
        self.completed_calls = 0

    def play_correct(self):
        self.correct_calls += 1

    def play_wrong(self):
        self.wrong_calls += 1

    def play_completed(self):
        self.completed_calls += 1


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.data_manager = _DataManagerStub()
        self.sound_manager = _SoundManagerStub()
        self.last_scene = None

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class TangramFusionSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_home_filter_choice_starts_glasses_session(self):
        scene = TangramFusionScene(_ManagerStub())
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_rl.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)
        self.assertEqual(scene.filter_direction, "left_blue_right_red")

    def test_correct_option_scores_and_advances_after_animation(self):
        manager = _ManagerStub()
        scene = TangramFusionScene(manager)
        scene._start_game()
        initial_round = scene.round_index
        scene.selected_option = scene.round_data["correct_option"]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertEqual(manager.sound_manager.correct_calls, 1)
        scene.pending_next_round_at = time.time() - 0.01
        scene.update()
        self.assertGreater(scene.round_index, initial_round)

    def test_wrong_option_counts_failure(self):
        manager = _ManagerStub()
        scene = TangramFusionScene(manager)
        scene._start_game()
        wrong = (scene.round_data["correct_option"] + 1) % 3
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.option_rects[wrong].center)])
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_filter_direction_changes_render(self):
        scene = TangramFusionScene(_ManagerStub())
        scene._start_game()
        first = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        second = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.filter_direction = "left_red_right_blue"
        scene.draw(first)
        scene.filter_direction = "left_blue_right_red"
        scene.draw(second)
        self.assertNotEqual(pygame.image.tostring(first, "RGBA"), pygame.image.tostring(second, "RGBA"))

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = TangramFusionScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "fusion.tangram_fusion")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_reset_returns_scene_to_home_state(self):
        scene = TangramFusionScene(_ManagerStub())
        scene._start_game()
        scene.selected_option = 2
        scene.feedback_text = "dirty"
        scene.reset()
        self.assertEqual(scene.state, scene.STATE_HOME)
        self.assertEqual(scene.round_index, 0)
        self.assertEqual(scene.selected_option, 0)
        self.assertEqual(scene.feedback_text, "")
        self.assertEqual(scene.round_data, {})

    def test_play_background_uses_magenta_glasses_color(self):
        scene = TangramFusionScene(_ManagerStub())
        scene._start_game()
        surface = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.draw(surface)
        self.assertEqual(surface.get_at((4, 4))[:3], GLASSES_BACKGROUND[:3])
