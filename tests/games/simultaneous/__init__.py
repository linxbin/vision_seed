from pathlib import Path
__path__.append(str(Path(__file__).resolve().parents[3] / 'games' / 'simultaneous'))
from games.simultaneous.eye_find_patterns.game import build_descriptor as build_eye_find_patterns_descriptor
from games.simultaneous.pong.game import build_descriptor as build_pong_descriptor
from games.simultaneous.spot_difference.game import build_descriptor as build_spot_difference_descriptor
