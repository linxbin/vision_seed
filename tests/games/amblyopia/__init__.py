from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "amblyopia"))

from games.amblyopia.precision_aim.game import build_descriptor as build_precision_aim_descriptor

