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

    # First Platoon
    SquadController.add_squad(gs, Vec2(110, 60), command)
    SquadController.add_squad(gs, Vec2(110, 75), command)
    SquadController.add_squad(gs, Vec2(110, 90), command)

    # Second Platoon
    SquadController.add_squad(gs, Vec2(140, 60), command)
    SquadController.add_squad(gs, Vec2(140, 75), command)
    SquadController.add_squad(gs, Vec2(140, 90), command)

    # Third Platoon
    SquadController.add_squad(gs, Vec2(170, 60), command)
    SquadController.add_squad(gs, Vec2(170, 75), command)
    SquadController.add_squad(gs, Vec2(170, 90), command)

    # Northern Road Buildings
    TerrainController.add_building(gs, Vec2(461, 366), 55)
    TerrainController.add_building(gs, Vec2(387, 432), -35)
    TerrainController.add_building(gs, Vec2(338, 481), -45)
    TerrainController.add_building(gs, Vec2(515, 372), -25)

    # Middle Road Buildings
    TerrainController.add_building(gs, Vec2(587, 456), -20)
    TerrainController.add_building(gs, Vec2(515, 500), 50)
    TerrainController.add_building(gs, Vec2(607, 415), 70)

    # Southern Road Buildings
    TerrainController.add_building(gs, Vec2(425, 512), 45)
    TerrainController.add_building(gs, Vec2(598, 598), 0)
    TerrainController.add_building(gs, Vec2(435, 528), 135)

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
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(463, 529),
        vertices=[
            Vec2(0, 0),
            Vec2(39, -42),
            Vec2(66, -63),
            Vec2(108, -83),
            Vec2(187, -108),
            Vec2(250, -128),
            Vec2(297, -131),
            Vec2(339, -128),
            Vec2(375, -120),
            Vec2(407, -100),
            Vec2(429, -78),
            Vec2(435, -68),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    # Northern Woods
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
        pivot=Vec2(282, 52),
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
        pivot=Vec2(762, 268),
        vertices=[
            Vec2(0, 0),
            Vec2(29, -21),
            Vec2(76, -75),
            Vec2(102, -134),
            Vec2(115, -148),
            Vec2(122, -146),
            Vec2(129, -138),
            Vec2(128, -123),
            Vec2(105, -75),
            Vec2(65, -16),
            Vec2(30, 20),
            Vec2(7, 30),
            Vec2(-3, 29),
            Vec2(-10, 23),
            Vec2(-11, 13),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(531, 222),
        vertices=[
            Vec2(0, 0),
            Vec2(-20, 15),
            Vec2(-31, 39),
            Vec2(-33, 70),
            Vec2(-26, 93),
            Vec2(-11, 106),
            Vec2(17, 106),
            Vec2(52, 96),
            Vec2(113, 78),
            Vec2(143, 61),
            Vec2(148, 44),
            Vec2(148, 22),
            Vec2(138, -2),
            Vec2(128, -22),
            Vec2(106, -32),
            Vec2(81, -36),
            Vec2(47, -25),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(637, 31),
        vertices=[
            Vec2(0, 0),
            Vec2(-8, 34),
            Vec2(-21, 48),
            Vec2(-45, 71),
            Vec2(-58, 102),
            Vec2(-59, 136),
            Vec2(-38, 145),
            Vec2(5, 150),
            Vec2(42, 140),
            Vec2(81, 114),
            Vec2(83, 99),
            Vec2(77, 32),
            Vec2(60, 4),
            Vec2(43, -9),
            Vec2(18, -10),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    # Village Woods
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(740, 421),
        vertices=[
            Vec2(0, 0),
            Vec2(-27, 11),
            Vec2(-43, 38),
            Vec2(-40, 85),
            Vec2(-8, 96),
            Vec2(34, 93),
            Vec2(69, 65),
            Vec2(115, 40),
            Vec2(115, 22),
            Vec2(102, 9),
            Vec2(52, -1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(547, 358),
        vertices=[
            Vec2(0, 0),
            Vec2(44, -24),
            Vec2(148, -55),
            Vec2(171, -51),
            Vec2(185, -40),
            Vec2(184, -21),
            Vec2(163, -13),
            Vec2(111, -4),
            Vec2(55, 13),
            Vec2(36, 28),
            Vec2(20, 29),
            Vec2(1, 24),
            Vec2(-5, 11),
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
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(737, 381),
        vertices=[
            Vec2(0, 0),
            Vec2(33, -1),
            Vec2(69, 5),
            Vec2(100, 13),
            Vec2(130, 20),
            Vec2(144, 19),
            Vec2(155, 13),
            Vec2(158, -2),
            Vec2(152, -20),
            Vec2(137, -37),
            Vec2(107, -46),
            Vec2(74, -49),
            Vec2(33, -42),
            Vec2(11, -31),
            Vec2(-5, -16),
            Vec2(-8, -8),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    # Northern Farmlands
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

    # Northern Field Hedges
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

    # Southern Farmlands
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(293, 701),
        vertices=[
            Vec2(0, 0),
            Vec2(5, 1),
            Vec2(10, 3),
            Vec2(37, 25),
            Vec2(84, 52),
            Vec2(101, 59),
            Vec2(103, 62),
            Vec2(102, 66),
            Vec2(82, 117),
            Vec2(61, 167),
            Vec2(56, 178),
            Vec2(51, 179),
            Vec2(37, 173),
            Vec2(-43, 120),
            Vec2(-64, 107),
            Vec2(-80, 96),
            Vec2(-82, 92),
            Vec2(-76, 83),
            Vec2(-23, 24),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(417, 569),
        vertices=[
            Vec2(0, 0),
            Vec2(-5, 3),
            Vec2(-17, 13),
            Vec2(-34, 29),
            Vec2(-44, 40),
            Vec2(-70, 73),
            Vec2(-96, 99),
            Vec2(-95, 106),
            Vec2(-72, 120),
            Vec2(-27, 140),
            Vec2(-10, 149),
            Vec2(-4, 149),
            Vec2(0, 146),
            Vec2(6, 132),
            Vec2(23, 97),
            Vec2(37, 67),
            Vec2(48, 40),
            Vec2(49, 36),
            Vec2(47, 33),
            Vec2(26, 16),
            Vec2(8, 3),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(541, 620),
        vertices=[
            Vec2(0, 0),
            Vec2(2, 3),
            Vec2(3, 10),
            Vec2(0, 52),
            Vec2(-6, 119),
            Vec2(-8, 132),
            Vec2(-11, 133),
            Vec2(-56, 126),
            Vec2(-89, 116),
            Vec2(-111, 112),
            Vec2(-112, 109),
            Vec2(-106, 88),
            Vec2(-79, 27),
            Vec2(-68, -2),
            Vec2(-64, -10),
            Vec2(-54, -12),
            Vec2(-30, -9),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(425, 739),
        vertices=[
            Vec2(0, 0),
            Vec2(25, 2),
            Vec2(60, 13),
            Vec2(104, 20),
            Vec2(107, 22),
            Vec2(108, 28),
            Vec2(103, 105),
            Vec2(101, 143),
            Vec2(96, 182),
            Vec2(94, 190),
            Vec2(89, 191),
            Vec2(36, 177),
            Vec2(-20, 164),
            Vec2(-56, 153),
            Vec2(-59, 150),
            Vec2(-57, 139),
            Vec2(-40, 92),
            Vec2(-23, 53),
            Vec2(-9, 20),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(676, 634),
        vertices=[
            Vec2(0, 0),
            Vec2(3, 1),
            Vec2(5, 7),
            Vec2(9, 42),
            Vec2(9, 60),
            Vec2(14, 95),
            Vec2(15, 106),
            Vec2(15, 115),
            Vec2(15, 118),
            Vec2(12, 122),
            Vec2(-3, 121),
            Vec2(-39, 119),
            Vec2(-66, 118),
            Vec2(-76, 117),
            Vec2(-78, 114),
            Vec2(-78, 103),
            Vec2(-73, 61),
            Vec2(-71, 38),
            Vec2(-69, 6),
            Vec2(-68, 2),
            Vec2(-67, -1),
            Vec2(-55, -2),
            Vec2(-36, -2),
            Vec2(-13, 0),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(596, 786),
        vertices=[
            Vec2(0, 0),
            Vec2(3, -4),
            Vec2(6, -6),
            Vec2(29, -5),
            Vec2(63, -3),
            Vec2(87, -3),
            Vec2(97, -3),
            Vec2(98, -2),
            Vec2(101, 2),
            Vec2(101, 7),
            Vec2(102, 16),
            Vec2(107, 67),
            Vec2(112, 116),
            Vec2(113, 128),
            Vec2(111, 131),
            Vec2(99, 132),
            Vec2(41, 131),
            Vec2(5, 129),
            Vec2(-7, 128),
            Vec2(-9, 126),
            Vec2(-10, 122),
            Vec2(-9, 104),
            Vec2(-4, 67),
            Vec2(-4, 43),
            Vec2(-1, 8),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(780, 618),
        vertices=[
            Vec2(0, 0),
            Vec2(4, 1),
            Vec2(10, 11),
            Vec2(14, 22),
            Vec2(20, 35),
            Vec2(24, 42),
            Vec2(35, 67),
            Vec2(40, 76),
            Vec2(50, 99),
            Vec2(63, 124),
            Vec2(63, 129),
            Vec2(61, 131),
            Vec2(46, 137),
            Vec2(12, 144),
            Vec2(-43, 152),
            Vec2(-50, 151),
            Vec2(-53, 149),
            Vec2(-55, 132),
            Vec2(-59, 99),
            Vec2(-63, 75),
            Vec2(-68, 30),
            Vec2(-67, 25),
            Vec2(-61, 19),
            Vec2(-27, 7),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(730, 783),
        vertices=[
            Vec2(0, 0),
            Vec2(3, -6),
            Vec2(33, -10),
            Vec2(76, -17),
            Vec2(115, -29),
            Vec2(122, -23),
            Vec2(140, 22),
            Vec2(161, 66),
            Vec2(167, 90),
            Vec2(167, 93),
            Vec2(162, 96),
            Vec2(96, 115),
            Vec2(44, 127),
            Vec2(20, 129),
            Vec2(16, 127),
            Vec2(11, 121),
            Vec2(7, 68),
            Vec2(3, 31),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    # Southern Field Building
    TerrainController.add_building(gs, Vec2(403, 768), -70)
    TerrainController.add_building(gs, Vec2(582, 767), 10)

    # Southern Woods & Hedges
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(555, 639),
        vertices=[
            Vec2(0, 0),
            Vec2(-7, 7),
            Vec2(-8, 22),
            Vec2(-10, 43),
            Vec2(-13, 56),
            Vec2(-17, 97),
            Vec2(-17, 112),
            Vec2(-7, 118),
            Vec2(5, 119),
            Vec2(21, 116),
            Vec2(36, 110),
            Vec2(39, 101),
            Vec2(44, 72),
            Vec2(45, 54),
            Vec2(41, 27),
            Vec2(39, 7),
            Vec2(33, 0),
            Vec2(14, -3),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(364, 561),
        vertices=[
            Vec2(0, 0),
            Vec2(-24, 9),
            Vec2(-57, 13),
            Vec2(-75, 20),
            Vec2(-80, 38),
            Vec2(-69, 54),
            Vec2(-46, 58),
            Vec2(-22, 56),
            Vec2(-4, 48),
            Vec2(19, 30),
            Vec2(22, 19),
            Vec2(22, 7),
            Vec2(12, -1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(325, 680),
        vertices=[
            Vec2(0, 0),
            Vec2(-10, 0),
            Vec2(-22, 5),
            Vec2(-24, 14),
            Vec2(-16, 24),
            Vec2(7, 43),
            Vec2(44, 64),
            Vec2(68, 73),
            Vec2(76, 73),
            Vec2(83, 68),
            Vec2(87, 58),
            Vec2(84, 47),
            Vec2(72, 36),
            Vec2(44, 23),
            Vec2(22, 13),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(598, 765),
        vertices=[],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(688, 644),
        vertices=[
            Vec2(0, 0),
            Vec2(-4, 2),
            Vec2(-5, 11),
            Vec2(-3, 27),
            Vec2(-1, 44),
            Vec2(-1, 60),
            Vec2(4, 94),
            Vec2(6, 121),
            Vec2(11, 143),
            Vec2(14, 174),
            Vec2(16, 206),
            Vec2(19, 237),
            Vec2(22, 259),
            Vec2(24, 266),
            Vec2(34, 266),
            Vec2(45, 265),
            Vec2(50, 259),
            Vec2(47, 214),
            Vec2(43, 165),
            Vec2(40, 137),
            Vec2(35, 117),
            Vec2(31, 72),
            Vec2(25, 36),
            Vec2(22, 11),
            Vec2(21, 4),
            Vec2(16, 1),
            Vec2(8, -1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(604, 755),
        vertices=[
            Vec2(0, 0),
            Vec2(-5, 6),
            Vec2(-7, 16),
            Vec2(-5, 21),
            Vec2(7, 23),
            Vec2(36, 24),
            Vec2(67, 25),
            Vec2(82, 24),
            Vec2(86, 16),
            Vec2(85, 10),
            Vec2(79, 5),
            Vec2(46, 1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs=gs,
        pivot=Vec2(36, 737),
        vertices=[
            Vec2(0, 0),
            Vec2(75, -25),
            Vec2(101, -40),
            Vec2(137, -76),
            Vec2(143, -94),
            Vec2(142, -110),
            Vec2(130, -121),
            Vec2(107, -123),
            Vec2(73, -122),
            Vec2(47, -117),
            Vec2(26, -106),
            Vec2(-5, -82),
            Vec2(-26, -58),
            Vec2(-37, -37),
            Vec2(-40, -19),
            Vec2(-33, -6),
            Vec2(-18, 1),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    return gs
