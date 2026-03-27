from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "amblyopia"))

from games.amblyopia.precision_aim.game import build_descriptor as build_precision_aim_descriptor
from games.amblyopia.whack_a_mole.game import build_descriptor as build_whack_a_mole_descriptor
from games.amblyopia.fruit_slice.game import build_descriptor as build_fruit_slice_descriptor

