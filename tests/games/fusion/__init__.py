from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "fusion"))

from games.fusion.push_box.game import build_descriptor as build_push_box_descriptor
from games.fusion.tetris.game import build_descriptor as build_tetris_descriptor
from games.fusion.path_fusion.game import build_descriptor as build_path_fusion_descriptor
from games.fusion.tangram_fusion.game import build_descriptor as build_tangram_fusion_descriptor

