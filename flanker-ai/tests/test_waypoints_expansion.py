from dataclasses import dataclass

import pytest
from flanker_ai.states.common.ai_points_expansion_service import (
    AiPointsExpansionService,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import GetLosPolygonOverrideComponent


def mock_get_los_polygon(
    gs: GameState,
    spotter_pos: Vec2,
    radius: float = 1000,
    jitter_size: float = 0.000001,
) -> list[Vec2]:
    """
    Mock LOS polygon sits between waypoint (0, 10) and (10, 10).
    """
    return [
        Vec2(12, 12),
        Vec2(4, 12),
        Vec2(4, 8),
        Vec2(12, 8),
        Vec2(12, 12),
    ]


@dataclass
class Fixture:
    gs: GameState
    waypoints_coodinates: list[Vec2]


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()

    # Terrain passes between wappoints (0, 10) and (10, 10).
    # Intersect at (6, 10)
    _ = gs.add_entity(
        Transform(Vec2(0, 0)),
        TerrainFeature(
            vertices=[
                Vec2(-6, 12),
                Vec2(6, 12),
                Vec2(6, 8),
                Vec2(-6, 8),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
        GetLosPolygonOverrideComponent(method=mock_get_los_polygon),
    )

    # Boundary box terrain
    _ = gs.add_entity(
        Transform(Vec2(0, 0)),
        TerrainFeature(
            vertices=[
                Vec2(-15, -15),
                Vec2(15, -15),
                Vec2(15, 15),
                Vec2(-15, 15),
            ],
            flag=TerrainFeature.Flag.BOUNDARY,
        ),
    )
    return Fixture(
        gs=gs,
        waypoints_coodinates=[
            Vec2(10, 10),
            Vec2(0, 10),
            Vec2(10, 0),
        ],
    )


def test_one_iteration(fixture: Fixture) -> None:
    new_waypoints = AiPointsExpansionService.expand_waypoints_line_based(
        gs=fixture.gs,
        initial_waypoints=fixture.waypoints_coodinates,
        tolerance=0,
    )
    assert set(fixture.waypoints_coodinates).issubset(
        new_waypoints
    ), "The initial waypoints must be inside the new waypoints."
    assert len(new_waypoints) == 10, "Expects 7 new waypoints and 3 existing ones."

    # Upper segment intersects both terrain and LOS
    assert Vec2(2, 10) in new_waypoints, "Expects a segment at (0, 10) to (4, 10)."
    assert Vec2(5, 10) in new_waypoints, "Expects a segment at (4, 10) to (6, 10)."
    assert Vec2(8, 10) in new_waypoints, "Expects a segment at (6, 10) to (10, 10)."

    # Left diagonal segment intersects terrain
    assert Vec2(1, 9) in new_waypoints, "Expects a segment at (2, 8) to (10, 10)."
    assert Vec2(6, 4) in new_waypoints, "Expects a segment at (2, 8) to (10, 0)."

    # Right vertical segment intersects LOS
    assert Vec2(10, 9) in new_waypoints, "Expects a segment at (10, 8) to (10, 10)."
    assert Vec2(10, 4) in new_waypoints, "Expects a segment at (10, 8) to (10, 0)."
