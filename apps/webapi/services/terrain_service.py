from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import MapBoundary, TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from webapi.models.components import TerrainTypeTag
from webapi.models.state_models import MapViewState, TerrainModel, TerrainType


class TerrainService:
    """Provides static methods to manipulate and query terrain features."""

    @staticmethod
    def get_terrain_flags(
        terrain_type: TerrainType,
    ) -> TerrainFeature.Flag:
        """Return the flags for a given terrain type."""
        match terrain_type:
            case TerrainType.FOREST:
                return TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE
            case TerrainType.ROAD:
                return TerrainFeature.Flag.WALKABLE | TerrainFeature.Flag.DRIVABLE
            case TerrainType.FIELD:
                return TerrainFeature.Flag.WALKABLE
            case TerrainType.WATER:
                return TerrainFeature.Flag.WATER
            case TerrainType.BUILDING:
                return TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE
            case _:
                raise ValueError(f"Unknown terrain type: {terrain_type}")

    @staticmethod
    def get_terrains(
        gs: GameState,
    ) -> list[TerrainModel]:
        """Get all terrain features from the game state."""
        terrains: list[TerrainModel] = []
        for ent, transform, terrain_feature, terrain_tag in gs.query(
            Transform, TerrainFeature, TerrainTypeTag
        ):
            terrains.append(
                TerrainModel(
                    terrain_id=ent,
                    position=transform.position,
                    degrees=transform.degrees,
                    vertices=terrain_feature.vertices,
                    terrain_type=terrain_tag.type,
                )
            )
        return terrains

    @staticmethod
    def get_map(
        gs: GameState,
    ) -> MapViewState:
        return MapViewState(
            terrains=TerrainService.get_terrains(gs),
            boundary=[
                vertex
                for _, boundary in gs.query(MapBoundary)
                for vertex in boundary.vertices
            ],
        )

    @staticmethod
    def add_terrain(
        gs: GameState,
        terrain: TerrainModel,
    ) -> None:
        """Add a new terrain feature to the game state."""
        gs.add_entity(
            Transform(position=terrain.position, degrees=0),
            TerrainFeature(
                vertices=terrain.vertices,
                flag=TerrainService.get_terrain_flags(terrain.terrain_type),
            ),
            TerrainTypeTag(terrain.terrain_type),
            id=terrain.terrain_id,
        )

    @staticmethod
    def delete_terrain(
        gs: GameState,
        terrain_id: UUID,
    ) -> None:
        # Make sure the terrain exists
        if gs.try_component(terrain_id, TerrainFeature) is None:
            raise ValueError(f"Terrain {terrain_id=} does not exist")
        # Then delete
        gs.delete_entity(terrain_id)

    @staticmethod
    def add_building(
        gs: GameState,
        position: Vec2,
        degrees: float,
    ) -> None:
        """Add a building terrain feature to the game state."""
        gs.add_entity(
            Transform(position=position, degrees=degrees),
            TerrainFeature(
                vertices=[
                    Vec2(-10, 5),
                    Vec2(10, 5),
                    Vec2(10, -5),
                    Vec2(-10, -5),
                ],
                flag=TerrainService.get_terrain_flags(TerrainType.BUILDING),
            ),
            TerrainTypeTag(TerrainType.BUILDING),
        )

    @staticmethod
    def update_terrain(
        gs: GameState,
        terrain_model: TerrainModel,
    ) -> None:
        transform = gs.get_component(terrain_model.terrain_id, Transform)
        terrain = gs.get_component(terrain_model.terrain_id, TerrainFeature)
        tag = gs.get_component(terrain_model.terrain_id, TerrainTypeTag)
        transform.position = terrain_model.position
        transform.degrees = terrain_model.degrees
        terrain.vertices = terrain_model.vertices
        terrain.flag = TerrainService.get_terrain_flags(terrain_model.terrain_type)
        tag.type = terrain_model.terrain_type
