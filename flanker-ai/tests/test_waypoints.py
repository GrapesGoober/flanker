from dataclasses import dataclass

import pytest
from flanker_ai.states.waypoints_actions import WaypointMoveAction
from flanker_ai.states.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeState


@dataclass
class Fixture:
    state: WaypointsState
    unit_move: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    unit_move = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -10)),
        FireControls(),
    )
    # Have the shooters stand on top of each other,
    # so the reactive fire position is the same
    gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(15, 20)),
    )
    gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(15, 20)),
    )

    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
                Vec2(0, 0),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )
    # 2000x2000 boundary
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-1000, -1000),
                Vec2(1000, -1000),
                Vec2(1000, 1000),
                Vec2(-1000, 1000),
                Vec2(-1000, -1000),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    state = WaypointsState(
        points=[
            Vec2(6, -10),
            Vec2(7, -10),
            Vec2(8, -10),
            Vec2(10, -10),
        ],
        path_tolerance=20,
    )

    state.initialize_state(gs)
    state.update_state(gs)

    return Fixture(state=state, unit_move=unit_move)


def test_interrupt_waypoint(fixture: Fixture) -> None:
    """Test that if there's move interrupt coodinates, they're are correct"""

    actions = fixture.state.get_actions()
    one_interrupt_found = False
    for action in actions:
        if not isinstance(action, WaypointMoveAction):
            continue
        interrupts = fixture.state.get_move_interrupts(
            action.unit_id,
            action.move_to_waypoint_id,
        )
        if interrupts == []:
            continue
        one_interrupt_found = True
        waypoint = fixture.state.waypoints[interrupts[0][0]]
        assert waypoint.position == Vec2(
            8, -10
        ), "Move action expects to be interrupted at (8, -10)"
    if not one_interrupt_found:
        assert False, "An interrupt must be found for this fixture"


def test_permutations(fixture: Fixture) -> None:
    """Test that the permutations from an interrupt are correct"""

    # Use any move action with an interrupt to run this test
    intended_move_action: WaypointMoveAction | None = None
    actions = fixture.state.get_actions()
    actions = fixture.state.get_actions()
    for action in actions:
        if not isinstance(action, WaypointMoveAction):
            continue
        interrupts = fixture.state.get_move_interrupts(
            action.unit_id,
            action.move_to_waypoint_id,
        )
        if interrupts == []:
            continue
        waypoint = fixture.state.waypoints[interrupts[0][0]]
        assert waypoint.position == Vec2(
            8, -10
        ), "Move action expects to be interrupted at (8, -10)"

        if waypoint.position == Vec2(8, -10):
            intended_move_action = action
            break

    assert (
        intended_move_action is not None
    ), "Can't test, interrupt move action doesn't exist"

    allowable_scores = [
        -3,  # +ACTIVE - ACTIVE - ACTIVE
        -4,  # +PINNED - ACTIVE - ACTIVE
        -5,  # +SUPPRESSED - ACTIVE - ACTIVE
        -6,  # 0 - ACTIVE - ACTIVE
    ]

    branches = fixture.state.get_branches(intended_move_action)
    for _, branch in branches:
        score = branch.get_score(InitiativeState.Faction.BLUE)
        assert score in allowable_scores, """Invalid states found"""
