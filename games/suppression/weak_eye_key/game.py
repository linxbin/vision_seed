from core.game_contract import GameDescriptor
from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene

CONFIG = ArcadeGameConfig(
    game_id="suppression.weak_eye_key",
    category="suppression",
    name="Weak Eye Key Hunt",
    name_key="game.suppression.weak_eye_key",
    title_key="weak_eye_key.title",
    subtitle_key="weak_eye_key.subtitle",
    guide_key="weak_eye_key.play.guide",
    metric_label_key="weak_eye_key.metric.label",
    help_steps=("weak_eye_key.help.step1", "weak_eye_key.help.step2", "weak_eye_key.help.step3"),
    mechanic_type="weak_eye_key",
    theme_color=(188, 122, 96),
    difficulty_level=4,
)


def create_scene(manager):
    return ArcadeTrainingScene(manager, CONFIG)


def build_descriptor():
    return GameDescriptor(
        game_id=CONFIG.game_id,
        category=CONFIG.category,
        name=CONFIG.name,
        factory=create_scene,
        name_key=CONFIG.name_key,
    )
