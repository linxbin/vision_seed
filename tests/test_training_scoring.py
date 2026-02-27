import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.training_scene import TrainingScene


class _SoundStub:
    def play_correct(self):
        pass

    def play_wrong(self):
        pass

    def set_enabled(self, _enabled):
        pass


class _DataStub:
    def __init__(self):
        self.saved = []

    def save_training_session(self, session_data):
        self.saved.append(session_data)
        return True


class _ManagerStub:
    def __init__(self, total_questions=1, start_level=3):
        self.settings = {
            "total_questions": total_questions,
            "start_level": start_level,
            "sound_enabled": False,
            "language": "en-US",
        }
        self.current_result = {"correct": 0, "wrong": 0, "total": 0, "duration": 0.0}
        self.sound_manager = _SoundStub()
        self.data_manager = _DataStub()
        self.last_scene = None

    def apply_sound_preference(self):
        pass

    def set_scene(self, name):
        self.last_scene = name


class TrainingScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_finish_after_single_correct_answer(self):
        manager = _ManagerStub(total_questions=1, start_level=3)
        scene = TrainingScene(manager)
        scene.target_direction = "UP"
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)

        scene.handle_events([event])

        self.assertEqual(manager.current_result["correct"], 1)
        self.assertEqual(manager.current_result["wrong"], 0)
        self.assertEqual(manager.current_result["total"], 1)
        self.assertEqual(manager.last_scene, "report")
        self.assertEqual(len(manager.data_manager.saved), 1)

    def test_zero_questions_finishes_immediately(self):
        manager = _ManagerStub(total_questions=0, start_level=3)
        TrainingScene(manager)

        self.assertEqual(manager.last_scene, "report")
        self.assertEqual(manager.current_result["total"], 0)
        self.assertEqual(len(manager.data_manager.saved), 1)


if __name__ == "__main__":
    unittest.main()
