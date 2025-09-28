from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from core.action_models import AssaultOutcomes, FireOutcomes
from core.utils.vec2 import Vec2


@dataclass
class Transform:
    """
    Holds spatial data for 2D entities. Used by rendering, movement,
    combat mechanics, etc. The existence of this component implies
    that the entity can be visualized in 2D space.
    """

    position: Vec2
    degrees: float = 0


@dataclass
class InitiativeState:
    """
    Singleton component that keeps track of faction & initiatives.
    """

    class Faction(Enum):
        BLUE = "BLUE"
        RED = "RED"

    faction: Faction = Faction.BLUE


@dataclass
class CombatUnit:
    """
    Marks an entity as a direct combat-capable unit.
    Tracks unit suppression and command hierarchy tree.
    """

    class Status(Enum):
        ACTIVE = "ACTIVE"
        PINNED = "PINNED"
        SUPPRESSED = "SUPPRESSED"

    faction: InitiativeState.Faction
    command_id: int | None = None
    status: Status = Status.ACTIVE
    inside_terrains: list[int] | None = None


@dataclass
class MoveControls:
    """
    Marks entity as movable, along with its. Used by move action to
    determine which terrain can or cannot cross.
    """

    class MoveType(Enum):
        FOOT = "FOOT"

    move_type: MoveType = MoveType.FOOT
    ...


@dataclass
class FireControls:
    """
    Marks an entity as capable for fire action.
    Defines the set of outcomes and override.
    """

    class OutcomesProbabilityRanges(float, Enum):
        """Each fire outcome and its probability range"""

        MISS = 0.3
        PIN = 0.7
        SUPPRESS = 0.95
        KILL = 1.0

    override: FireOutcomes | None = None
    can_reactive_fire: bool = True


@dataclass
class AssaultControls:
    """
    Marks an entity as capable for assault action.
    Defines the RNG roll multiplier.
    """

    class SuccessChances(float, Enum):
        """Chance of successful assault per each target status."""

        ACTIVE = 0.5
        PINNED = 0.7
        SUPPRESSED = 0.95

    override: AssaultOutcomes | None = None


@dataclass
class TerrainFeature:
    """
    Represents a polygonal terrain feature with terrain type bit flags.
    Bit flags are used to determine LOS, movement, and fire types.
    """

    vertices: list[Vec2]
    is_closed_loop: bool = True
    flag: int = -1

    class Flag(IntFlag):
        """Bit flags for allowable terrain feature properties."""

        NONE = 0  # Important: Start with 0 for no flags
        OPAQUE = auto()
        WALKABLE = auto()
        DRIVABLE = auto()
        WATER = auto()
        HILL = auto()


@dataclass
class EliminationObjective:
    """
    Represents the enemy elimination objective for a given faction.
    """

    target_faction: InitiativeState.Faction
    winning_faction: InitiativeState.Faction
    units_to_destroy: int
    units_destroyed_counter: int
