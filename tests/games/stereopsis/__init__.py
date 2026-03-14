from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "stereopsis"))

from games.stereopsis.depth_grab.game import build_descriptor as build_depth_grab_descriptor

