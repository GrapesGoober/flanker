from backend.tag_components import TerrainTypeTag
from core.components import TerrainFeature, Transform
from core.utils.vec2 import Vec2
from core.gamestate import GameState
from backend.models import TerrainModel


class TerrainService:
    """Provides static methods to manipulate and query terrain features."""

    @staticmethod
    def get_terrain_flags(terrain_type: TerrainModel.Types) -> TerrainFeature.Flag:
        """Return the flags for a given terrain type."""
        match terrain_type:
            case TerrainModel.Types.FOREST:
                return TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE
            case TerrainModel.Types.ROAD:
                return TerrainFeature.Flag.WALKABLE | TerrainFeature.Flag.DRIVABLE
            case TerrainModel.Types.FIELD:
                return TerrainFeature.Flag.WALKABLE
            case TerrainModel.Types.WATER:
                return TerrainFeature.Flag.WATER
            case TerrainModel.Types.BUILDING:
                return TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE
            case _:
                raise ValueError(f"Unknown terrain type: {terrain_type}")

    @staticmethod
    def get_terrains(gs: GameState) -> list[TerrainModel]:
        """Get all terrain features from the game state."""
        terrains: list[TerrainModel] = []
        for ent, transform, terrain_feature, terrain_tag in gs.query(
            Transform, TerrainFeature, TerrainTypeTag
        ):
            terrains.append(
                TerrainModel(
                    feature_id=ent,
                    position=transform.position,
                    degrees=transform.degrees,
                    vertices=terrain_feature.vertices,
                    terrain_type=terrain_tag.type,
                )
            )
        return terrains

    @staticmethod
    def add_terrain(
        gs: GameState,
        pivot: Vec2,
        vertices: list[Vec2],
        terrain_type: TerrainModel.Types,
    ) -> None:
        """Add a new terrain feature to the game state."""
        gs.add_entity(
            Transform(position=pivot, degrees=0),
            TerrainFeature(
                vertices=vertices,
                flag=TerrainService.get_terrain_flags(terrain_type),
            ),
            TerrainTypeTag(terrain_type),
        )

    @staticmethod
    def add_building(gs: GameState, position: Vec2, degrees: float) -> None:
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
                flag=TerrainService.get_terrain_flags(TerrainModel.Types.BUILDING),
            ),
            TerrainTypeTag(TerrainModel.Types.BUILDING),
        )

    @staticmethod
    def update_terrain(gs: GameState, body: TerrainModel) -> None:
        transform = gs.get_component(body.feature_id, Transform)
        feature = gs.get_component(body.feature_id, TerrainFeature)
        tag = gs.get_component(body.feature_id, TerrainTypeTag)
        transform.position = body.position
        transform.degrees = body.degrees
        feature.vertices = body.vertices
        feature.flag = TerrainService.get_terrain_flags(body.terrain_type)
        tag.type = body.terrain_type
