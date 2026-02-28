import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.training_scene import TrainingScene


class _SoundStub:
    def __init__(self):
        self.completed_calls = 0
        self.completed_length = 0.0

    def play_correct(self):
        pass

    def play_wrong(self):
        pass

    def play_completed(self):
        self.completed_calls += 1
        return self.completed_length

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

    def t(self, key, **kwargs):
        return key


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

        self.assertTrue(scene.finish_transition_active)
        self.assertIsNone(manager.last_scene)
        self.assertEqual(len(manager.data_manager.saved), 0)

        scene.finish_transition_ends_at = time.time() - 0.01
        scene.update()

        self.assertEqual(manager.current_result["correct"], 1)
        self.assertEqual(manager.current_result["wrong"], 0)
        self.assertEqual(manager.current_result["total"], 1)
        self.assertEqual(manager.last_scene, "report")
        self.assertEqual(len(manager.data_manager.saved), 1)
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_enter_skips_finish_transition(self):
        manager = _ManagerStub(total_questions=1, start_level=3)
        scene = TrainingScene(manager)
        scene.target_direction = "UP"

        answer_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        skip_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

        scene.handle_events([answer_event])
        self.assertTrue(scene.finish_transition_active)

        scene.handle_events([skip_event])
        self.assertFalse(scene.finish_transition_active)
        self.assertEqual(manager.last_scene, "report")
        self.assertEqual(len(manager.data_manager.saved), 1)
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_finish_waits_for_completed_audio_length(self):
        manager = _ManagerStub(total_questions=1, start_level=3)
        manager.sound_manager.completed_length = 0.8
        scene = TrainingScene(manager)
        scene.target_direction = "UP"

        answer_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        scene.handle_events([answer_event])

        self.assertTrue(scene.finish_transition_active)
        self.assertIsNone(manager.last_scene)
        self.assertEqual(manager.sound_manager.completed_calls, 1)

        # 仍在音频时长内，不应跳转
        scene.finish_transition_ends_at = time.time() + 0.2
        scene.update()
        self.assertIsNone(manager.last_scene)

        # 超过结束时间后跳转
        scene.finish_transition_ends_at = time.time() - 0.01
        scene.update()
        self.assertEqual(manager.last_scene, "report")

    def test_finish_transition_caps_long_audio_duration(self):
        manager = _ManagerStub(total_questions=1, start_level=3)
        manager.sound_manager.completed_length = 5.0
        scene = TrainingScene(manager)
        scene.target_direction = "UP"

        answer_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        scene.handle_events([answer_event])

        remaining = scene.finish_transition_ends_at - time.time()
        self.assertGreaterEqual(remaining, 1.0)
        self.assertLessEqual(remaining, 1.25)

    def test_finish_transition_floors_short_audio_duration(self):
        manager = _ManagerStub(total_questions=1, start_level=3)
        manager.sound_manager.completed_length = 0.1
        scene = TrainingScene(manager)
        scene.target_direction = "UP"

        answer_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        scene.handle_events([answer_event])

        remaining = scene.finish_transition_ends_at - time.time()
        self.assertGreaterEqual(remaining, 0.30)
        self.assertLessEqual(remaining, 0.45)

    def test_zero_questions_finishes_immediately(self):
        manager = _ManagerStub(total_questions=0, start_level=3)
        TrainingScene(manager)

        self.assertEqual(manager.last_scene, "report")
        self.assertEqual(manager.current_result["total"], 0)
        self.assertEqual(len(manager.data_manager.saved), 1)
        self.assertEqual(manager.sound_manager.completed_calls, 0)

    def test_pause_blocks_answer_until_resumed(self):
        manager = _ManagerStub(total_questions=2, start_level=3)
        scene = TrainingScene(manager)
        scene.target_direction = "UP"

        pause_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
        answer_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)

        scene.handle_events([pause_event])
        self.assertTrue(scene.is_paused)

        scene.handle_events([answer_event])
        self.assertEqual(scene.current, 0)
        self.assertEqual(scene.correct, 0)

        scene.handle_events([pause_event])
        self.assertFalse(scene.is_paused)

        scene.handle_events([answer_event])
        self.assertEqual(scene.current, 1)
        self.assertEqual(scene.correct, 1)


if __name__ == "__main__":
    unittest.main()
