import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "sound_enabled": True}
        self.active_game_id = "amblyopia.precision_aim"
        self.active_category = "amblyopia"
        self.current_result = {}
        self.data_manager = type("DataManager", (), {"save_training_session": lambda self, payload: payload})()
        self.sound_manager = type("SoundManager", (), {"play_correct": lambda self: None, "play_wrong": lambda self: None, "play_completed": lambda self: None})()

    def t(self, key, **kwargs):
        return key

    def set_scene(self, name):
        self.last_scene = name

    def apply_sound_preference(self):
        return None


class ArcadeTrainingMechanicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_precision_aim_target_shrinks_faster_mid_round(self):
        manager = _ManagerStub()
        config = ArcadeGameConfig(
            game_id="amblyopia.precision_aim",
            category="amblyopia",
            name="Precision Aim Target",
            name_key="game.amblyopia.precision_aim",
            title_key="precision_aim.title",
            subtitle_key="precision_aim.subtitle",
            guide_key="precision_aim.play.guide",
            metric_label_key="precision_aim.metric.label",
            help_steps=("precision_aim.help.step1", "precision_aim.help.step2", "precision_aim.help.step3"),
            mechanic_type="precision_aim",
            theme_color=(208, 104, 104),
            difficulty_level=4,
        )
        scene = ArcadeTrainingScene(manager, config)
        scene.current_round = 0
        scene.mechanic.start_round()
        base_radius = scene.mechanic.base_radius
        scene.round_elapsed = scene.config.round_seconds * 0.5
        scene.mechanic.update(0.0)

        self.assertLessEqual(scene.mechanic.current_radius, int(base_radius * 0.72))
        self.assertGreaterEqual(scene.mechanic.current_radius, 10)


if __name__ == "__main__":
    unittest.main()
