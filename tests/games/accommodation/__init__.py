from pathlib import Path
__path__.append(str(Path(__file__).resolve().parents[3] / 'games' / 'accommodation'))
from .e_orientation import build_descriptor
