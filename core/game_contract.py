from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable


@runtime_checkable
class SceneProtocol(Protocol):
    def handle_events(self, events):
        ...

    def update(self):
        ...

    def draw(self, screen):
        ...

    def on_resize(self, width, height):
        ...

    def reset(self):
        ...


GameFactory = Callable[[object], SceneProtocol]


@dataclass(frozen=True)
class GameDescriptor:
    game_id: str
    category: str
    name: str
    factory: GameFactory
    name_key: str = ""
