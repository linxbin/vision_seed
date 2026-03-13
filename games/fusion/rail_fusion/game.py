from core.game_contract import GameDescriptor
from games.common.binocular_fusion.scene import FusionGameConfig, FusionTrainingScene

CONFIG = FusionGameConfig(
    game_id="fusion.rail_fusion",
    category="fusion",
    name="Rail Fusion",
    name_key="game.fusion.rail_fusion",
    title_key="rail_fusion.title",
    subtitle_key="rail_fusion.subtitle",
    guide_key="rail_fusion.play.guide",
    metric_label_key="rail_fusion.metric.label",
    help_steps=("rail_fusion.help.step1", "rail_fusion.help.step2", "rail_fusion.help.step3"),
    mechanic_type="rail_fusion",
    theme_color=(122, 152, 214),
)


def create_scene(manager):
    return FusionTrainingScene(manager, CONFIG)


def build_descriptor():
    return GameDescriptor(
        game_id=CONFIG.game_id,
        category=CONFIG.category,
        name=CONFIG.name,
        factory=create_scene,
        name_key=CONFIG.name_key,
    )
