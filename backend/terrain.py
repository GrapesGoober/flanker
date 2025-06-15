from core.components import TerrainFeature, Transform
from core.vec2 import Vec2
from core.gamestate import GameState
from backend.models import TerrainModel
from core.transform_utils import TransformUtils


class TerrainController:

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
            case _:
                raise ValueError(f"Unknown terrain type: {terrain_type}")

    @staticmethod
    def get_terrain_type(flags: int) -> TerrainModel.Types:
        if flags == (TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE):
            return TerrainModel.Types.FOREST
        elif flags == (TerrainFeature.Flag.WALKABLE | TerrainFeature.Flag.DRIVABLE):
            return TerrainModel.Types.ROAD
        elif flags == TerrainFeature.Flag.WALKABLE:
            return TerrainModel.Types.FIELD
        elif flags == TerrainFeature.Flag.WATER:
            return TerrainModel.Types.WATER
        else:
            raise ValueError(f"Unknown terrain flags: {flags}")

    @staticmethod
    def add_terrain(
        gs: GameState, vertices: list[Vec2], terrain_type: TerrainModel.Types
    ) -> None:
        pivot = vertices[0]
        gs.add_entity(
            Transform(position=pivot, angle=0),
            TerrainFeature(
                vertices=TransformUtils.translate(vertices, pivot * -1),
                flag=TerrainController.get_terrain_flags(terrain_type),
            ),
        )

    @staticmethod
    def get_terrains(gs: GameState) -> list[TerrainModel]:
        terrains: list[TerrainModel] = []
        for ent, feat, transform in gs.query(TerrainFeature, Transform):
            terrains.append(
                TerrainModel(
                    feature_id=ent,
                    vertices=TransformUtils.translate(
                        feat.vertices, transform.position
                    ),
                    terrain_type=TerrainController.get_terrain_type(feat.flag),
                )
            )
        return terrains
