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
    SquadController.add_squad(gs, Vec2(120, 160), command)
    SquadController.add_squad(gs, Vec2(180, 260), command)

    # Add terrains
    TerrainController.add_terrain(
        gs,
        [
            Vec2(532, 581),
            Vec2(482, 636),
            Vec2(486, 656),
            Vec2(521, 697),
            Vec2(559, 696),
            Vec2(587, 680),
            Vec2(581, 624),
            Vec2(593, 608),
            Vec2(593, 589),
            Vec2(551, 571),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(765, 489),
            Vec2(698, 528),
            Vec2(697, 551),
            Vec2(738, 576),
            Vec2(746, 585),
            Vec2(772, 590),
            Vec2(847, 564),
            Vec2(890, 554),
            Vec2(898, 543),
            Vec2(889, 509),
            Vec2(835, 477),
            Vec2(797, 475),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(383, 502),
            Vec2(369, 508),
            Vec2(368, 531),
            Vec2(361, 623),
            Vec2(356, 633),
            Vec2(361, 637),
            Vec2(371, 637),
            Vec2(379, 627),
            Vec2(376, 610),
            Vec2(384, 583),
            Vec2(383, 530),
            Vec2(388, 518),
            Vec2(388, 508),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(396, 497),
            Vec2(391, 513),
            Vec2(396, 520),
            Vec2(418, 520),
            Vec2(469, 527),
            Vec2(547, 548),
            Vec2(552, 542),
            Vec2(548, 532),
            Vec2(417, 506),
            Vec2(409, 499),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(388, 525),
            Vec2(381, 633),
            Vec2(388, 643),
            Vec2(465, 637),
            Vec2(477, 636),
            Vec2(529, 578),
            Vec2(540, 568),
            Vec2(540, 552),
            Vec2(469, 530),
            Vec2(403, 522),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(510, 712),
            Vec2(462, 642),
            Vec2(404, 643),
            Vec2(361, 664),
            Vec2(308, 679),
            Vec2(276, 713),
            Vec2(297, 789),
            Vec2(314, 804),
            Vec2(400, 806),
            Vec2(463, 794),
            Vec2(514, 738),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs,
        [
            Vec2(327, 663),
            Vec2(299, 670),
            Vec2(270, 704),
            Vec2(243, 707),
            Vec2(112, 660),
            Vec2(99, 649),
            Vec2(88, 592),
            Vec2(96, 575),
            Vec2(157, 533),
            Vec2(181, 539),
            Vec2(208, 568),
            Vec2(233, 583),
            Vec2(263, 588),
            Vec2(290, 605),
            Vec2(325, 633),
            Vec2(330, 645),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(255, 364),
            Vec2(228, 374),
            Vec2(207, 389),
            Vec2(221, 416),
            Vec2(246, 423),
            Vec2(268, 404),
            Vec2(273, 381),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs,
        [
            Vec2(170, 527),
            Vec2(215, 548),
            Vec2(244, 575),
            Vec2(279, 587),
            Vec2(328, 612),
            Vec2(342, 622),
            Vec2(347, 618),
            Vec2(354, 597),
            Vec2(364, 493),
            Vec2(373, 458),
            Vec2(366, 436),
            Vec2(332, 424),
            Vec2(275, 409),
            Vec2(247, 431),
            Vec2(218, 424),
            Vec2(203, 425),
            Vec2(165, 511),
        ],
        terrain_type=TerrainModel.Types.FIELD,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(163, 477),
            Vec2(147, 517),
            Vec2(100, 556),
            Vec2(65, 567),
            Vec2(32, 542),
            Vec2(8, 495),
            Vec2(39, 434),
            Vec2(91, 422),
            Vec2(134, 433),
            Vec2(150, 449),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
    TerrainController.add_terrain(
        gs,
        [
            Vec2(9, 558),
            Vec2(47, 568),
            Vec2(72, 592),
            Vec2(79, 648),
            Vec2(119, 684),
            Vec2(211, 715),
            Vec2(267, 732),
            Vec2(291, 807),
            Vec2(282, 839),
            Vec2(231, 854),
            Vec2(134, 914),
            Vec2(84, 917),
            Vec2(28, 893),
            Vec2(-144, 794),
            Vec2(-161, 746),
            Vec2(-132, 666),
            Vec2(-52, 655),
            Vec2(-22, 601),
            Vec2(-16, 564),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(-68, 623),
            Vec2(-33, 569),
            Vec2(-10, 482),
            Vec2(28, 411),
            Vec2(99, 356),
            Vec2(180, 337),
            Vec2(278, 341),
            Vec2(373, 382),
            Vec2(434, 425),
            Vec2(517, 480),
            Vec2(616, 506),
            Vec2(685, 503),
            Vec2(794, 456),
            Vec2(864, 450),
            Vec2(1014, 472),
            Vec2(1098, 523),
            Vec2(1168, 582),
            Vec2(1268, 648),
            Vec2(1344, 585),
            Vec2(1248, 501),
            Vec2(1162, 446),
            Vec2(1035, 386),
            Vec2(882, 356),
            Vec2(801, 360),
            Vec2(680, 404),
            Vec2(623, 411),
            Vec2(538, 393),
            Vec2(417, 313),
            Vec2(295, 273),
            Vec2(169, 250),
            Vec2(82, 250),
            Vec2(40, 272),
            Vec2(-35, 355),
            Vec2(-70, 443),
            Vec2(-104, 509),
            Vec2(-160, 519),
            Vec2(-202, 516),
            Vec2(-260, 540),
            Vec2(-336, 668),
            Vec2(-362, 760),
            Vec2(-284, 801),
            Vec2(-245, 722),
            Vec2(-188, 656),
        ],
        terrain_type=TerrainModel.Types.WATER,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(777, 790),
            Vec2(668, 698),
            Vec2(650, 672),
            Vec2(650, 553),
            Vec2(649, 514),
            Vec2(639, 390),
            Vec2(607, 295),
            Vec2(577, 273),
            Vec2(480, 251),
            Vec2(366, 195),
            Vec2(225, 146),
            Vec2(152, 84),
            Vec2(142, 61),
            Vec2(148, 26),
            Vec2(226, -138),
            Vec2(227, -196),
            Vec2(213, -324),
        ],
        terrain_type=TerrainModel.Types.ROAD,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(751, 209),
            Vec2(687, 237),
            Vec2(674, 294),
            Vec2(673, 355),
            Vec2(726, 361),
            Vec2(837, 326),
            Vec2(903, 327),
            Vec2(948, 300),
            Vec2(946, 252),
            Vec2(864, 200),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    TerrainController.add_terrain(
        gs,
        [
            Vec2(579, 207),
            Vec2(597, 233),
            Vec2(649, 246),
            Vec2(686, 222),
            Vec2(690, 206),
            Vec2(668, 184),
            Vec2(624, 170),
            Vec2(601, 179),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    return gs
