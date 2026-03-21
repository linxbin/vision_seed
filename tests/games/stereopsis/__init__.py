from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "games" / "stereopsis"))

from games.stereopsis.depth_grab.game import build_descriptor as build_depth_grab_descriptor
from games.stereopsis.brick_breaker.game import build_descriptor as build_brick_breaker_descriptor
from games.stereopsis.frogger.game import build_descriptor as build_frogger_descriptor
from games.stereopsis.ring_flight.game import build_descriptor as build_ring_flight_descriptor

