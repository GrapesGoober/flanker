from enum import IntFlag, auto
from systems.ecs import Entity, GameState
from systems.event import Listener
from systems.polygon import Polygon
from systems.vec2 import Vec2
from domain.interface import TerrainType, TerrainFeatureGetInput


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


class TerrainFeature(Entity):
    def __init__(
        self, gs: GameState, terrain_type: TerrainType, coordinates: list[Vec2]
    ) -> None:
        self.terrain_type = terrain_type
        self.coordinates = coordinates
        super().__init__(
            gs,
            Polygon(coordinates, flag=to_flags(terrain_type)),
            Listener(TerrainFeatureGetInput, self.on_get),
        )

    def on_get(self, e: TerrainFeatureGetInput) -> TerrainFeatureGetInput.Response:
        return TerrainFeatureGetInput.Response(
            terrain_type=self.terrain_type, coordinates=self.coordinates
        )
