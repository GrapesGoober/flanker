from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from uuid import UUID

from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
from flanker_core.models.vec2 import Vec2


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
    command_id: UUID | None = None
    status: Status = Status.ACTIVE


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

    override: FireOutcomes | None = None
    can_reactive_fire: bool = True


@dataclass
class AssaultControls:
    """
    Marks an entity as capable for assault action.
    Defines the RNG roll multiplier.
    """

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
        BOUNDARY = auto()


@dataclass
class EliminationWinCondition:
    """
    Represents the elimination winning condition for a given faction.
    Once the provided faction eliminates enough of the target faction,
    the provided winning faction is considered winner.
    """

    target_faction: InitiativeState.Faction
    winning_faction: InitiativeState.Faction
    units_to_eliminate: int
    units_eliminated_counter: int


@dataclass
class StallLoseCondition:
    """
    Represents stall losing condition for a given faction.
    Once the faction performs enough stalling moves, the provided
    winning faction is considered winner.
    """

    counting_faction: InitiativeState.Faction
    winning_faction: InitiativeState.Faction
    stall_count: int
    stall_limit: int
