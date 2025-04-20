from enum import Enum, IntFlag, auto


class TerrainType(Enum):
    """Supported terrain types."""

    FOREST = "FOREST"
    ROAD = "ROAD"
    FIELD = "FIELD"


class TerrainFlag(IntFlag):
    """Bit flags for Geometry system bitmasking. Useful for intersection properties."""

    NONE = 0  # Important: Start with 0 for no flags
    OPAQUE = auto()
    WALKABLE = auto()
    DRIVABLE = auto()
    WATER = auto()
    HILL = auto()


def to_flags(type: TerrainType) -> TerrainFlag:
    """Maps a Terrain Type to its bitflag properties."""
    FLAGS: dict[TerrainType, TerrainFlag] = {
        TerrainType.FOREST: TerrainFlag.OPAQUE | TerrainFlag.WALKABLE,
        TerrainType.ROAD: TerrainFlag.WALKABLE | TerrainFlag.DRIVABLE,
        TerrainType.FIELD: TerrainFlag.WALKABLE,
    }
    return FLAGS[type]
