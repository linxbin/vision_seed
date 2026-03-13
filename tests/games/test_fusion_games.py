import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.fusion.bridge_fusion.game import build_descriptor as build_bridge_fusion_descriptor
from games.fusion.puzzle_fusion.game import build_descriptor as build_puzzle_fusion_descriptor
from games.fusion.rail_fusion.game import build_descriptor as build_rail_fusion_descriptor


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
    def __init__(self, game_id):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.active_game_id = game_id
        self.active_category = "fusion"
        self.current_result = {}
        self.last_scene = None
        self.data_manager = _DataManagerStub()
        self.sound_manager = _SoundManagerStub()

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class FusionGamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_fusion_games_support_help_glasses_and_result_save(self):
        surface = pygame.Surface((900, 700))
        for descriptor in (
            build_puzzle_fusion_descriptor(),
            build_bridge_fusion_descriptor(),
            build_rail_fusion_descriptor(),
        ):
            manager = _ManagerStub(descriptor.game_id)
            scene = descriptor.factory(manager)
            scene.on_resize(900, 700)
            scene.draw(surface)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)])
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)])
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            self.assertEqual(scene.state, scene.STATE_HELP)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            self.assertEqual(scene.state, scene.STATE_HOME)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)])
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            self.assertTrue(scene.show_filter_picker)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
            self.assertEqual(scene.filter_direction, scene.FILTER_RL)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            self.assertEqual(scene.state, scene.STATE_PLAY)
            scene.mechanic.start_task()
            if hasattr(scene.mechanic, "offset"):
                scene.mechanic.offset = 0
            if hasattr(scene.mechanic, "current_state"):
                scene.mechanic.current_state = scene.mechanic.correct_state
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
            self.assertEqual(manager.sound_manager.correct_calls, 1)
            scene.session_started_at = time.time() - scene._session_seconds()
            scene.update()
            self.assertEqual(scene.state, scene.STATE_RESULT)
            self.assertEqual(manager.data_manager.saved[-1]["game_id"], descriptor.game_id)
            self.assertEqual(manager.sound_manager.completed_calls, 1)


if __name__ == "__main__":
    unittest.main()
