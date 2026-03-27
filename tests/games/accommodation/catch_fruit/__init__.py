from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[4] / "games" / "accommodation" / "catch_fruit"))

from games.accommodation.catch_fruit.game import build_descriptor

