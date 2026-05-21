from dataclasses import dataclass

import pytest
from flanker_ai.states.waypoints.waypoints_generator_service import (
    WaypointsGeneratorService,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState, TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.register_systems import register_systems


@dataclass
class Fixture:
    gs: GameState
    waypoints_coodinates: list[Vec2]


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    register_systems(gs)
    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
    )
    _ = gs.add_entity(
        Transform(Vec2(0, 0)),
        TerrainFeature(
            vertices=[
                Vec2(8, 5),
                Vec2(6, 5),
                Vec2(6, 7),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )

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
            Vec2(10, 0),
            Vec2(0, 10),
        ],
    )


def test_one_iteration(fixture: Fixture) -> None:
    new_waypoints = WaypointsGeneratorService.expand_waypoints_interrupt(
        gs=fixture.gs,
        initial_waypoints=fixture.waypoints_coodinates,
        iterations=1,
    )
    assert set(fixture.waypoints_coodinates).issubset(
        new_waypoints
    ), "The initial waypoints must be inside the new waypoints."
    assert len(new_waypoints) == 9, "Expects 9 total waypoints"

    # Floating point imprecision makes me uneasy about this test

    def assert_waypoint_in(waypoints: list[Vec2], expected: Vec2) -> None:
        assert any(
            (expected - waypoint).length() < 1e-3 for waypoint in waypoints
        ), f"Expected waypoint {expected} not found in waypoints."

    assert_waypoint_in(new_waypoints, Vec2(2, 10))
    assert_waypoint_in(new_waypoints, Vec2(6, 10))
    assert_waypoint_in(new_waypoints, Vec2(10, 5 / 3))
    assert_waypoint_in(new_waypoints, Vec2(4.28571, 5.71429))
    assert_waypoint_in(new_waypoints, Vec2(7.14286, 2.85714))
