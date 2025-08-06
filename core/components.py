from dataclasses import dataclass
from enum import Enum, IntFlag, auto
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
class CombatUnit:
    """
    Marks an entity as a direct combat-capable unit.
    Tracks unit suppression and command hierarchy tree.
    """

    class Status(Enum):
        ACTIVE = "ACTIVE"
        PINNED = "PINNED"
        SUPPRESSED = "SUPPRESSED"

    command_id: int
    status: Status = Status.ACTIVE


@dataclass
class Faction:
    """
    Marks a unit as a faction commander. Entity with this component
    is expected to be the root node of the command hierarchy tree.
    """

    has_initiative: bool


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
    Defines the fire type and set of outcomes.
    """

    class Outcomes(float, Enum):
        MISS = 0.3
        PIN = 0.7
        SUPPRESS = 0.95
        KILL = 1.0

    override: Outcomes | None = None
    can_reactive_fire: bool = True


@dataclass
class TerrainFeature:
    """
    Represents a polygonal terrain feature with terrain type bit flags.
    Bit flags are used to determine LOS, movement, and fire types.
    """

    vertices: list[Vec2]
    flag: int = -1

    class Flag(IntFlag):
        """Bit flags for allowable terrain feature properties."""

        NONE = 0  # Important: Start with 0 for no flags
        OPAQUE = auto()
        WALKABLE = auto()
        DRIVABLE = auto()
        WATER = auto()
        HILL = auto()
