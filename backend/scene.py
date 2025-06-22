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
        [
            Vec2(73, 170),
            Vec2(86, 189),
            Vec2(104, 214),
            Vec2(134, 244),
            Vec2(162, 271),
            Vec2(183, 295),
            Vec2(216, 312),
            Vec2(236, 321),
            Vec2(257, 325),
            Vec2(286, 329),
            Vec2(319, 334),
            Vec2(375, 337),
            Vec2(402, 337),
            Vec2(444, 336),
            Vec2(481, 336),
            Vec2(549, 336),
            Vec2(592, 333),
            Vec2(623, 333),
            Vec2(659, 333),
            Vec2(698, 339),
            Vec2(733, 346),
            Vec2(763, 357),
            Vec2(795, 373),
            Vec2(825, 397),
            Vec2(852, 434),
            Vec2(875, 479),
            Vec2(889, 532),
            Vec2(911, 602),
            Vec2(923, 617),
            Vec2(922, 659),
            Vec2(910, 652),
            Vec2(900, 643),
            Vec2(887, 630),
            Vec2(876, 606),
            Vec2(862, 574),
            Vec2(857, 538),
            Vec2(851, 509),
            Vec2(837, 472),
            Vec2(814, 439),
            Vec2(789, 411),
            Vec2(757, 388),
            Vec2(724, 377),
            Vec2(688, 371),
            Vec2(655, 366),
            Vec2(626, 368),
            Vec2(585, 369),
            Vec2(540, 367),
            Vec2(506, 365),
            Vec2(473, 364),
            Vec2(430, 366),
            Vec2(384, 364),
            Vec2(328, 364),
            Vec2(289, 358),
            Vec2(247, 353),
            Vec2(205, 343),
            Vec2(169, 322),
            Vec2(139, 296),
            Vec2(115, 272),
            Vec2(81, 247),
            Vec2(63, 222),
            Vec2(47, 198),
            Vec2(27, 180),
            Vec2(12, 175),
            Vec2(0, 170),
            Vec2(0, 135),
            Vec2(17, 139),
            Vec2(36, 146),
            Vec2(52, 154),
            Vec2(66, 162),
        ],
        terrain_type=TerrainModel.Types.WATER,
    )

    # Roads
    TerrainController.add_terrain(
        gs,
        [
            Vec2(164, 2),
            Vec2(193, 96),
            Vec2(215, 168),
            Vec2(234, 230),
            Vec2(234, 241),
            Vec2(218, 300),
            Vec2(197, 361),
            Vec2(188, 392),
            Vec2(189, 404),
            Vec2(196, 412),
            Vec2(219, 436),
            Vec2(245, 460),
            Vec2(303, 516),
            Vec2(362, 574),
            Vec2(427, 633),
            Vec2(535, 737),
            Vec2(608, 806),
            Vec2(665, 847),
            Vec2(729, 892),
            Vec2(807, 937),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(220, 177),
            Vec2(262, 168),
            Vec2(315, 155),
            Vec2(330, 152),
            Vec2(341, 152),
            Vec2(399, 162),
            Vec2(464, 174),
            Vec2(530, 185),
            Vec2(593, 194),
            Vec2(661, 204),
            Vec2(673, 204),
            Vec2(709, 200),
            Vec2(775, 190),
            Vec2(837, 179),
            Vec2(904, 163),
            Vec2(925, 156),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    # Village fields
    TerrainController.add_terrain(
        gs,
        [
            Vec2(535, 262),
            Vec2(539, 266),
            Vec2(541, 273),
            Vec2(541, 285),
            Vec2(539, 303),
            Vec2(536, 327),
            Vec2(531, 331),
            Vec2(525, 332),
            Vec2(511, 332),
            Vec2(494, 332),
            Vec2(468, 330),
            Vec2(452, 329),
            Vec2(447, 327),
            Vec2(445, 322),
            Vec2(445, 315),
            Vec2(449, 287),
            Vec2(451, 273),
            Vec2(453, 263),
            Vec2(457, 258),
            Vec2(460, 257),
            Vec2(486, 257),
            Vec2(512, 260),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    # Village buildings
    TerrainController.add_building(gs, Vec2(232, 187), -0.1)
    TerrainController.add_building(gs, Vec2(549, 250), 1.7)

    # Village woods
    TerrainController.add_terrain(
        gs,
        [
            Vec2(496, 254),
            Vec2(471, 252),
            Vec2(458, 253),
            Vec2(451, 251),
            Vec2(446, 248),
            Vec2(447, 237),
            Vec2(452, 233),
            Vec2(466, 231),
            Vec2(487, 231),
            Vec2(515, 235),
            Vec2(532, 240),
            Vec2(535, 246),
            Vec2(534, 252),
            Vec2(530, 256),
            Vec2(512, 257),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(442, 252),
            Vec2(447, 255),
            Vec2(449, 260),
            Vec2(447, 270),
            Vec2(443, 289),
            Vec2(439, 308),
            Vec2(439, 319),
            Vec2(432, 323),
            Vec2(425, 326),
            Vec2(421, 322),
            Vec2(419, 312),
            Vec2(421, 293),
            Vec2(425, 277),
            Vec2(427, 266),
            Vec2(432, 253),
            Vec2(437, 250),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    return gs
