from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "fusion"))

from games.fusion.push_box.game import build_descriptor as build_push_box_descriptor

