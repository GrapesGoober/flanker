from dataclasses import dataclass
from core.utils.vec2 import Vec2


@dataclass
class MoveActionInput:
    unit_id: int
    to: Vec2


@dataclass
class FireActionInput:
    attacker_id: int
    target_id: int


@dataclass
class MoveStepEvent:

    unit_id: int
    is_interrupted: bool = False
