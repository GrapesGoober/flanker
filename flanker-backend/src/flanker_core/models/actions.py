from dataclasses import dataclass
from uuid import UUID

from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
from flanker_core.models.vec2 import Vec2


@dataclass
class MoveAction:
    """
    Moves a unit to a destination. This pivots toward the movement path
    first. Movement draws reactive fires, which may interrupt the move
    and can lose initiative.
    """

    unit_id: UUID
    to: Vec2


@dataclass
class PivotAction:
    """
    Pivots a unit toward a destination. Pivoting draws reactive fires
    and can lose initiative. Pivoting always complete regardless
    """

    unit_id: UUID
    to: Vec2


@dataclass
class FireAction:
    """
    Fires at an enemy unit. The target must be within line of sight.
    Fire modifies the target's status and creates a persistent fire effect.
    A failed fire can lose initiative.
    """

    unit_id: UUID
    target_id: UUID


@dataclass
class AssaultAction:
    """
    Moves a unit toward a target and performs an assault on arrival.
    Movement draws reactive fires, which may interrupt the move.
    The loser of the assault is killed.
    """

    unit_id: UUID
    target_id: UUID


@dataclass
class MoveActionResult:
    move_interrupted: bool
    reactive_fire_outcomes: list[FireOutcomes]


@dataclass
class PivotActionResult:
    reactive_fire_outcomes: list[FireOutcomes]


@dataclass
class FireActionResult:
    outcome: FireOutcomes | None


@dataclass
class AssaultActionResult:
    outcome: AssaultOutcomes | None
    reactive_fire_outcomes: list[FireOutcomes]


Action = MoveAction | PivotAction | FireAction | AssaultAction
ActionResult = (
    MoveActionResult | PivotActionResult | FireActionResult | AssaultActionResult
)
