from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "suppression"))

from games.suppression.weak_eye_key.game import build_descriptor as build_weak_eye_key_descriptor

