from dataclasses import dataclass
from uuid import UUID

from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
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
    unit_id: UUID
    target_id: UUID


@dataclass
class AssaultAction:
    unit_id: UUID
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


@dataclass
class AssaultActionResult:
    """Result of an assault action as assault outcome, and any reactive fire."""

    outcome: AssaultOutcomes | None = None
    reactive_fire_outcome: FireOutcomes | None = None


Actions = MoveAction | PivotAction | FireAction | AssaultAction
ActionResults = (
    MoveActionResult | PivotActionResult | FireActionResult | AssaultActionResult
)
