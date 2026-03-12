from pathlib import Path
__path__.append(str(Path(__file__).resolve().parents[3] / 'games' / 'accommodation'))
from .catch_fruit import build_descriptor as build_catch_fruit_descriptor
from .e_orientation import build_descriptor
