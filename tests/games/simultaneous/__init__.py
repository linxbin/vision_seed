from pathlib import Path
__path__.append(str(Path(__file__).resolve().parents[3] / 'games' / 'simultaneous'))
from .eye_find_patterns.game import build_descriptor as build_eye_find_patterns_descriptor
from .spot_difference import build_descriptor as build_spot_difference_descriptor
