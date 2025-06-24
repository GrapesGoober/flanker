from backend.models import TerrainModel
from backend.squad import SquadController
from backend.terrain import TerrainController
from core.vec2 import Vec2
from core.gamestate import GameState


def new_scene() -> GameState:
    """Initialize and return a `GameState` instance with predefined entities."""
    gs = GameState()

    # Add squads
    command = SquadController.add_command(gs, Vec2(100, 120))
    SquadController.add_squad(gs, Vec2(500, 800), command)

    # Village buildings
    TerrainController.add_building(gs, Vec2(387, 432), -35)
    TerrainController.add_building(gs, Vec2(461, 366), 55)

    # Roads
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(906, -94),
        vertices=[
            Vec2(0, 0),
            Vec2(-23, 139),
            Vec2(-76, 282),
            Vec2(-120, 335),
            Vec2(-215, 391),
            Vec2(-318, 421),
            Vec2(-424, 468),
            Vec2(-520, 544),
            Vec2(-584, 611),
            Vec2(-646, 684),
            Vec2(-718, 767),
            Vec2(-761, 805),
            Vec2(-867, 852),
            Vec2(-1009, 881),
            Vec2(-1129, 909),
            Vec2(-1223, 949),
            Vec2(-1316, 991),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(385, 454),
        vertices=[
            Vec2(0, 0),
            Vec2(89, 89),
            Vec2(136, 119),
            Vec2(191, 133),
            Vec2(251, 134),
            Vec2(302, 122),
            Vec2(339, 108),
            Vec2(474, 34),
            Vec2(600, -45),
            Vec2(727, -142),
            Vec2(800, -221),
            Vec2(874, -286),
            Vec2(982, -369),
            Vec2(1094, -447),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    # Woods
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(-8, 78),
        vertices=[
            Vec2(0, 0),
            Vec2(17, 24),
            Vec2(31, 70),
            Vec2(49, 96),
            Vec2(112, 130),
            Vec2(148, 158),
            Vec2(152, 180),
            Vec2(132, 210),
            Vec2(88, 225),
            Vec2(2, 216),
            Vec2(-63, 180),
            Vec2(-88, 128),
            Vec2(-83, 73),
            Vec2(-59, 30),
            Vec2(-36, 0),
            Vec2(-16, -5),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(130, 302),
        vertices=[
            Vec2(0, 0),
            Vec2(-7, 33),
            Vec2(-1, 61),
            Vec2(31, 80),
            Vec2(64, 79),
            Vec2(97, 62),
            Vec2(111, 34),
            Vec2(105, 0),
            Vec2(95, -21),
            Vec2(46, -34),
            Vec2(18, -28),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(262, 22),
        vertices=[
            Vec2(0, 0),
            Vec2(-6, 20),
            Vec2(-32, 107),
            Vec2(-74, 170),
            Vec2(-83, 184),
            Vec2(-83, 192),
            Vec2(-76, 197),
            Vec2(-61, 193),
            Vec2(-30, 155),
            Vec2(-11, 119),
            Vec2(5, 73),
            Vec2(16, 30),
            Vec2(16, 14),
            Vec2(10, -2),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(462, 418),
        vertices=[
            Vec2(0, 0),
            Vec2(-23, 21),
            Vec2(-51, 31),
            Vec2(-56, 41),
            Vec2(-44, 56),
            Vec2(-13, 58),
            Vec2(13, 52),
            Vec2(27, 37),
            Vec2(26, 16),
            Vec2(22, -2),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(227, 414),
        vertices=[
            Vec2(0, 0),
            Vec2(-14, 30),
            Vec2(-48, 53),
            Vec2(-104, 66),
            Vec2(-170, 66),
            Vec2(-189, 73),
            Vec2(-200, 82),
            Vec2(-198, 93),
            Vec2(-180, 98),
            Vec2(-156, 93),
            Vec2(-113, 90),
            Vec2(-71, 91),
            Vec2(-42, 87),
            Vec2(-23, 80),
            Vec2(6, 65),
            Vec2(17, 39),
            Vec2(25, 10),
            Vec2(25, -3),
            Vec2(16, -11),
            Vec2(10, -10),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(612, 513),
        vertices=[
            Vec2(0, 0),
            Vec2(-8, 8),
            Vec2(-23, 38),
            Vec2(-18, 56),
            Vec2(-7, 63),
            Vec2(31, 60),
            Vec2(40, 54),
            Vec2(48, 38),
            Vec2(50, 15),
            Vec2(40, 6),
            Vec2(18, -1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    # FIELDS
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(349, 414),
        vertices=[
            Vec2(0, 0),
            Vec2(9, 1),
            Vec2(36, -11),
            Vec2(49, -27),
            Vec2(7, -95),
            Vec2(-18, -132),
            Vec2(-27, -137),
            Vec2(-67, -120),
            Vec2(-89, -99),
            Vec2(-87, -92),
            Vec2(-43, -49),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(412, 360),
        vertices=[
            Vec2(0, 0),
            Vec2(8, 1),
            Vec2(37, -21),
            Vec2(54, -32),
            Vec2(55, -39),
            Vec2(46, -61),
            Vec2(37, -93),
            Vec2(31, -99),
            Vec2(-1, -90),
            Vec2(-25, -77),
            Vec2(-38, -67),
            Vec2(-38, -61),
            Vec2(-15, -26),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(360, 265),
        vertices=[
            Vec2(0, 0),
            Vec2(6, 4),
            Vec2(52, -13),
            Vec2(86, -21),
            Vec2(86, -29),
            Vec2(73, -81),
            Vec2(53, -162),
            Vec2(45, -168),
            Vec2(20, -156),
            Vec2(-35, -125),
            Vec2(-61, -105),
            Vec2(-61, -95),
            Vec2(-52, -78),
            Vec2(-25, -30),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    # Field Hedges
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(385, 327),
        vertices=[
            Vec2(0, 0),
            Vec2(22, 33),
            Vec2(30, 42),
            Vec2(33, 51),
            Vec2(32, 57),
            Vec2(26, 60),
            Vec2(17, 56),
            Vec2(10, 43),
            Vec2(0, 26),
            Vec2(-14, 5),
            Vec2(-25, -15),
            Vec2(-33, -24),
            Vec2(-41, -33),
            Vec2(-46, -41),
            Vec2(-47, -54),
            Vec2(-43, -58),
            Vec2(-36, -57),
            Vec2(-28, -47),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    return gs
