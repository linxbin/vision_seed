from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "suppression"))

from games.suppression.weak_eye_key.game import build_descriptor as build_weak_eye_key_descriptor
from games.suppression.find_same.game import build_descriptor as build_find_same_descriptor
from games.suppression.red_blue_catch.game import build_descriptor as build_red_blue_catch_descriptor

