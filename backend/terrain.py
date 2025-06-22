from dataclasses import dataclass
from core.components import TerrainFeature, Transform
from core.vec2 import Vec2
from core.gamestate import GameState
from backend.models import TerrainModel
from core.transform_utils import TransformUtils


class TerrainController:

    @dataclass
    class TypeTag:
        type: TerrainModel.Types

    @staticmethod
    def get_terrain_flags(terrain_type: TerrainModel.Types) -> TerrainFeature.Flag:
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
        terrains: list[TerrainModel] = []
        for ent, transform, terrain_feature, terrain_tag in gs.query(
            Transform, TerrainFeature, TerrainController.TypeTag
        ):
            terrains.append(
                TerrainModel(
                    feature_id=ent,
                    vertices=TransformUtils.apply(terrain_feature.vertices, transform),
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
        gs.add_entity(
            Transform(position=pivot, angle=0),
            TerrainFeature(
                vertices=vertices,
                flag=TerrainController.get_terrain_flags(terrain_type),
            ),
            TerrainController.TypeTag(terrain_type),
        )

    @staticmethod
    def add_building(gs: GameState, position: Vec2, angle: float) -> None:
        gs.add_entity(
            Transform(position=position, angle=angle),
            TerrainFeature(
                vertices=[
                    Vec2(-10, 5),
                    Vec2(10, 5),
                    Vec2(10, -5),
                    Vec2(-10, -5),
                ],
                flag=TerrainController.get_terrain_flags(TerrainModel.Types.BUILDING),
            ),
            TerrainController.TypeTag(TerrainModel.Types.BUILDING),
        )
