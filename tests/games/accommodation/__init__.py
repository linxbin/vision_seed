from pathlib import Path
__path__.append(str(Path(__file__).resolve().parents[3] / 'games' / 'accommodation'))
from games.accommodation.catch_fruit.game import build_descriptor as build_catch_fruit_descriptor
from games.accommodation.e_orientation.game import build_descriptor
