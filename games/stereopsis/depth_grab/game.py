from core.game_contract import GameDescriptor
from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene

CONFIG = ArcadeGameConfig(
    game_id="stereopsis.depth_grab",
    category="stereopsis",
    name="Depth Grab Stars",
    name_key="game.stereopsis.depth_grab",
    title_key="depth_grab.title",
    subtitle_key="depth_grab.subtitle",
    guide_key="depth_grab.play.guide",
    metric_label_key="depth_grab.metric.label",
    help_steps=("depth_grab.help.step1", "depth_grab.help.step2", "depth_grab.help.step3"),
    mechanic_type="depth_grab",
    theme_color=(132, 120, 222),
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
