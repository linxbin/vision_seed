import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "sound_enabled": True, "session_duration_minutes": 5}
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
        scene.session_elapsed = 0.0
        scene.mechanic.start_round()
        base_radius = scene.mechanic.base_radius
        scene.round_elapsed = scene.config.round_seconds * 0.5
        scene.mechanic.update(0.0)

        self.assertLessEqual(scene.mechanic.current_radius, int(base_radius * 0.72))
        self.assertGreaterEqual(scene.mechanic.current_radius, 10)

    def test_precision_aim_uses_smaller_base_radius_in_later_stage(self):
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
            rounds_total=9,
        )
        scene = ArcadeTrainingScene(manager, config)
        scene.session_elapsed = 0.0
        scene.mechanic.start_round()
        warmup_radius = scene.mechanic.base_radius
        scene.session_elapsed = scene._session_seconds() * 0.9
        scene.mechanic.start_round()
        challenge_radius = scene.mechanic.base_radius
        self.assertLess(challenge_radius, warmup_radius)

    def test_precision_aim_challenge_stage_target_drifts(self):
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
            rounds_total=9,
        )
        scene = ArcadeTrainingScene(manager, config)
        scene.session_elapsed = scene._session_seconds() * 0.9
        scene.mechanic.start_round()
        before = scene.mechanic.target_center
        scene.round_elapsed = scene.config.round_seconds * 0.5
        scene.mechanic.update(10.0)
        after = scene.mechanic.target_center
        self.assertNotEqual(before, after)

    def test_catch_fruit_combo_and_bonus_scoring(self):
        manager = _ManagerStub()
        config = ArcadeGameConfig(
            game_id="accommodation.catch_fruit",
            category="accommodation",
            name="Catch Fruit Focus",
            name_key="game.accommodation.catch_fruit",
            title_key="catch_fruit.title",
            subtitle_key="catch_fruit.subtitle",
            guide_key="catch_fruit.play.guide",
            metric_label_key="catch_fruit.metric.label",
            help_steps=("catch_fruit.help.step1", "catch_fruit.help.step2", "catch_fruit.help.step3"),
            mechanic_type="catch_fruit",
            theme_color=(96, 156, 104),
            difficulty_level=3,
        )
        scene = ArcadeTrainingScene(manager, config)
        scene._start_session()
        mechanic = scene.mechanic
        mechanic.streak = 2
        mechanic.best_streak = 2
        mechanic.fruit_asset_name = "watermelon"
        mechanic.fruit_x = mechanic.basket_x
        mechanic.fruit_y = scene.play_area.bottom - 45
        mechanic.update(0.0)
        self.assertTrue(mechanic.outcome)
        self.assertEqual(mechanic.score_for_outcome(True), 38)
        self.assertEqual(mechanic.best_streak, 3)
        self.assertEqual(mechanic.bonus_hits, 1)

    def test_precision_aim_quality_grades_center_hit(self):
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
        scene._start_session()
        mechanic = scene.mechanic
        mechanic.aim_center = [mechanic.target_center[0], mechanic.target_center[1]]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertEqual(mechanic.last_quality, "center")
        self.assertEqual(mechanic.score_for_outcome(True), 18)
        self.assertEqual(mechanic.best_center_streak, 1)

    def test_precision_aim_center_streak_adds_bonus_score(self):
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
        scene._start_session()
        mechanic = scene.mechanic
        mechanic.center_streak = 1
        mechanic.best_center_streak = 1
        mechanic.aim_center = [mechanic.target_center[0], mechanic.target_center[1]]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertEqual(mechanic.last_quality, "center")
        self.assertEqual(mechanic.score_for_outcome(True), 24)

    def test_arcade_play_area_uses_larger_layout(self):
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
        self.assertEqual(scene.play_area.y, 104)
        self.assertEqual(scene.play_area.height, 524)

    def test_amblyopia_play_background_switches_pattern(self):
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
            play_background_style="amblyopia_stimulus",
        )
        scene = ArcadeTrainingScene(manager, config)
        scene._start_session()
        scene.state = scene.STATE_PLAY
        scene.session_started_at = 97.0
        screen_a = pygame.Surface((scene.width, scene.height))
        screen_b = pygame.Surface((scene.width, scene.height))
        from unittest.mock import patch
        with patch("games.common.arcade_training.scene.time.time", return_value=100.0):
            scene.draw(screen_a)
        with patch("games.common.arcade_training.scene.time.time", return_value=104.0):
            scene.draw(screen_b)
        sample_points = [
            (scene.play_area.x + 28, scene.play_area.y + 28),
            (scene.play_area.x + 74, scene.play_area.y + 52),
            (scene.play_area.x + 126, scene.play_area.y + 88),
            (scene.play_area.x + 182, scene.play_area.y + 124),
            (scene.play_area.x + 238, scene.play_area.y + 160),
            (scene.play_area.x + 294, scene.play_area.y + 196),
            (scene.play_area.x + 350, scene.play_area.y + 232),
            (scene.play_area.x + 406, scene.play_area.y + 268),
        ]
        colors_a = [screen_a.get_at(point)[:3] for point in sample_points]
        colors_b = [screen_b.get_at(point)[:3] for point in sample_points]
        self.assertNotEqual(colors_a, colors_b)

    def test_amblyopia_stimulus_background_stays_inside_play_frame(self):
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
            play_background_style="amblyopia_stimulus",
        )
        scene = ArcadeTrainingScene(manager, config)
        scene._start_session()
        scene.state = scene.STATE_PLAY
        screen = pygame.Surface((scene.width, scene.height))
        with unittest.mock.patch("games.common.arcade_training.scene.time.time", return_value=100.0):
            scene.draw(screen)
        outside_point = (scene.play_area.x - 8, scene.play_area.y + 28)
        inside_point = (scene.play_area.x + 28, scene.play_area.y + 28)
        self.assertNotEqual(screen.get_at(outside_point)[:3], screen.get_at(inside_point)[:3])

    def test_default_play_background_stays_light_without_stimulus_style(self):
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
        scene._start_session()
        scene.state = scene.STATE_PLAY
        screen = pygame.Surface((scene.width, scene.height))
        scene.draw(screen)
        sample = screen.get_at((scene.play_area.x + 40, scene.play_area.y + 40))[:3]
        self.assertEqual(sample, (245, 250, 255))


if __name__ == "__main__":
    unittest.main()
