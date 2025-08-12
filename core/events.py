from dataclasses import dataclass
from core.utils.vec2 import Vec2


@dataclass
class MoveActionInput:
    unit_id: int
    to: Vec2
