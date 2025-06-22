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

    # Main river
    TerrainController.add_terrain(
        gs,
        pivot=Vec2(-2, 134),
        vertices=[
            Vec2(0, 0),
            Vec2(26, 5),
            Vec2(39, 10),
            Vec2(52, 16),
            Vec2(67, 25),
            Vec2(79, 39),
            Vec2(106, 81),
            Vec2(139, 113),
            Vec2(155, 130),
            Vec2(177, 153),
            Vec2(188, 163),
            Vec2(204, 171),
            Vec2(239, 187),
            Vec2(300, 196),
            Vec2(346, 201),
            Vec2(400, 203),
            Vec2(464, 201),
            Vec2(560, 201),
            Vec2(625, 198),
            Vec2(662, 199),
            Vec2(699, 204),
            Vec2(735, 211),
            Vec2(767, 223),
            Vec2(793, 236),
            Vec2(802, 242),
            Vec2(824, 260),
            Vec2(831, 268),
            Vec2(852, 297),
            Vec2(858, 306),
            Vec2(876, 343),
            Vec2(880, 353),
            Vec2(894, 408),
            Vec2(911, 461),
            Vec2(916, 471),
            Vec2(925, 482),
            Vec2(924, 526),
            Vec2(911, 517),
            Vec2(890, 499),
            Vec2(886, 492),
            Vec2(864, 444),
            Vec2(862, 433),
            Vec2(853, 379),
            Vec2(840, 343),
            Vec2(833, 331),
            Vec2(791, 279),
            Vec2(761, 257),
            Vec2(747, 250),
            Vec2(730, 246),
            Vec2(710, 241),
            Vec2(666, 234),
            Vec2(643, 233),
            Vec2(588, 235),
            Vec2(432, 233),
            Vec2(338, 231),
            Vec2(320, 230),
            Vec2(256, 221),
            Vec2(234, 217),
            Vec2(212, 212),
            Vec2(197, 206),
            Vec2(173, 191),
            Vec2(163, 184),
            Vec2(119, 142),
            Vec2(108, 134),
            Vec2(78, 106),
            Vec2(51, 68),
            Vec2(43, 60),
            Vec2(32, 51),
            Vec2(24, 45),
            Vec2(11, 42),
            Vec2(0, 40),
        ],
        terrain_type=TerrainModel.Types.WATER,
    )

    # Roads
    TerrainController.add_terrain(
        gs,
        pivot=Vec2(164, 2),
        vertices=[
            Vec2(0, 0),
            Vec2(70, 227),
            Vec2(71, 238),
            Vec2(24, 389),
            Vec2(26, 401),
            Vec2(202, 575),
            Vec2(443, 803),
            Vec2(568, 891),
            Vec2(642, 934),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    TerrainController.add_terrain(
        gs,
        pivot=Vec2(220, 177),
        vertices=[
            Vec2(0, 0),
            Vec2(110, -24),
            Vec2(120, -24),
            Vec2(315, 9),
            Vec2(438, 27),
            Vec2(454, 27),
            Vec2(638, -3),
            Vec2(703, -21),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    # Village fields
    TerrainController.add_terrain(
        gs,
        pivot=Vec2(461, 257),
        vertices=[
            Vec2(0, 0),
            Vec2(27, 1),
            Vec2(71, 5),
            Vec2(77, 7),
            Vec2(79, 11),
            Vec2(81, 21),
            Vec2(78, 48),
            Vec2(75, 71),
            Vec2(70, 73),
            Vec2(62, 74),
            Vec2(31, 74),
            Vec2(-9, 72),
            Vec2(-15, 70),
            Vec2(-16, 61),
            Vec2(-12, 26),
            Vec2(-8, 5),
            Vec2(-4, 0),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    # Village buildings
    TerrainController.add_building(gs, Vec2(240, 187), -15)
    TerrainController.add_building(gs, Vec2(549, 250), 100)

    # Village woods
    TerrainController.add_terrain(
        gs,
        pivot=Vec2(451, 232),
        vertices=[
            Vec2(0, 0),
            Vec2(17, -2),
            Vec2(35, -2),
            Vec2(62, 2),
            Vec2(78, 6),
            Vec2(83, 10),
            Vec2(85, 13),
            Vec2(84, 17),
            Vec2(81, 22),
            Vec2(76, 25),
            Vec2(60, 25),
            Vec2(44, 22),
            Vec2(20, 20),
            Vec2(6, 21),
            Vec2(-2, 18),
            Vec2(-6, 15),
            Vec2(-6, 5),
            Vec2(-4, 1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    return gs
