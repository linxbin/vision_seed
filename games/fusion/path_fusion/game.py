from core.game_contract import GameDescriptor
from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene

CONFIG = ArcadeGameConfig(
    game_id="fusion.path_fusion",
    category="fusion",
    name="Fusion Path Connect",
    name_key="game.fusion.path_fusion",
    title_key="path_fusion.title",
    subtitle_key="path_fusion.subtitle",
    guide_key="path_fusion.play.guide",
    metric_label_key="path_fusion.metric.label",
    help_steps=("path_fusion.help.step1", "path_fusion.help.step2", "path_fusion.help.step3"),
    mechanic_type="path_fusion",
    theme_color=(114, 132, 224),
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
