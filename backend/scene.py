from backend.assets import TerrainModel, add_squad, add_terrain
from core.vec2 import Vec2
from core.gamestate import GameState


def create_gamestate() -> GameState:
    """Initialize and return a `GameState` instance with predefined entities."""
    gs = GameState()

    # Add squads
    add_squad(gs, Vec2(120, 160))
    add_squad(gs, Vec2(180, 260))

    # Add terrains
    add_terrain(
        gs,
        [
            Vec2(100, 100),
            Vec2(130, 70),
            Vec2(170, 80),
            Vec2(200, 100),
            Vec2(220, 140),
            Vec2(200, 180),
            Vec2(160, 190),
            Vec2(110, 160),
            Vec2(100, 100),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    add_terrain(
        gs,
        [
            Vec2(308, 95),
            Vec2(313, 135),
            Vec2(346, 174),
            Vec2(389, 183),
            Vec2(447, 172),
            Vec2(488, 201),
            Vec2(507, 246),
            Vec2(526, 284),
            Vec2(580, 293),
            Vec2(628, 267),
            Vec2(646, 195),
            Vec2(655, 144),
            Vec2(632, 80),
            Vec2(574, 46),
            Vec2(504, 26),
            Vec2(430, 20),
            Vec2(368, 30),
            Vec2(334, 50),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    add_terrain(
        gs,
        [
            Vec2(-47, 159),
            Vec2(-21, 188),
            Vec2(-2, 229),
            Vec2(19, 276),
            Vec2(60, 307),
            Vec2(106, 322),
            Vec2(161, 326),
            Vec2(221, 312),
            Vec2(280, 289),
            Vec2(349, 254),
            Vec2(398, 262),
            Vec2(440, 283),
            Vec2(486, 319),
            Vec2(528, 351),
            Vec2(573, 388),
            Vec2(610, 434),
            Vec2(673, 475),
            Vec2(737, 480),
            Vec2(794, 475),
            Vec2(848, 448),
            Vec2(907, 418),
            Vec2(910, 459),
            Vec2(854, 485),
            Vec2(798, 507),
            Vec2(732, 517),
            Vec2(658, 508),
            Vec2(576, 467),
            Vec2(534, 415),
            Vec2(498, 386),
            Vec2(456, 362),
            Vec2(416, 341),
            Vec2(354, 328),
            Vec2(291, 349),
            Vec2(219, 365),
            Vec2(136, 371),
            Vec2(64, 361),
            Vec2(-12, 339),
            Vec2(-76, 287),
            Vec2(-108, 205),
            Vec2(-146, 120),
            Vec2(-161, 63),
            Vec2(-183, -15),
            Vec2(-135, -38),
            Vec2(-109, 20),
            Vec2(-82, 91),
        ],
        terrain_type=TerrainModel.Types.WATER,
    )

    add_terrain(
        gs,
        [
            Vec2(101, -160),
            Vec2(92, 16),
            Vec2(106, 27),
            Vec2(197, 35),
            Vec2(250, 43),
            Vec2(262, 53),
            Vec2(269, 256),
            Vec2(284, 370),
            Vec2(307, 499),
            Vec2(320, 507),
            Vec2(485, 503),
            Vec2(501, 502),
            Vec2(606, 519),
            Vec2(618, 527),
            Vec2(773, 633),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    add_terrain(
        gs,
        [Vec2(92, 16), Vec2(41, -19), Vec2(-45, -38), Vec2(-205, -70)],
        terrain_type=TerrainModel.Types.ROAD,
    )

    add_terrain(
        gs,
        [
            Vec2(308, 499),
            Vec2(277, 487),
            Vec2(117, 465),
            Vec2(-85, 436),
            Vec2(-100, 418),
            Vec2(-142, 236),
            Vec2(-190, 121),
            Vec2(-262, -157),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    return gs
