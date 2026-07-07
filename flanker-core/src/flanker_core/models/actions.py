from dataclasses import dataclass
from uuid import UUID

from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2


@dataclass
class MoveAction:
    unit_id: UUID
    to: Vec2


@dataclass
class PivotAction:
    unit_id: UUID
    to: Vec2


@dataclass
class FireAction:
    attacker_id: UUID
    target_id: UUID


@dataclass
class MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class PivotActionResult:
    """Result of a pivot action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class FireActionResult:
    """Result of a fire action as outcome."""

    outcome: FireOutcomes | None = None


Actions = MoveAction | PivotAction | FireAction
ActionResults = MoveActionResult | PivotActionResult | FireActionResult
