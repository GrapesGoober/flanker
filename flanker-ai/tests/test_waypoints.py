from dataclasses import dataclass

import pytest
from flanker_ai.states.waypoints_actions import WaypointMoveAction
from flanker_ai.states.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    FireOutcomes,
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
    enemy_1: int
    enemy_2: int
    enemy_3: int


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
    enemy_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(15, 20)),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(15, 20)),
    )
    # Have another enemy unit for a second reactive fire
    enemy_3 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(10, 20)),
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
            # TODO: fixturize the waypoint IDs, not hardcoded IDs
            Vec2(6, -10),  # 0
            Vec2(7, -10),  # 1
            Vec2(8, -10),  # 2
            Vec2(20, -10),  # 3
            # The unit positions would be separate IDs
        ],
        path_tolerance=20,
    )

    state.initialize_state(gs)
    state.update_state(gs)

    return Fixture(
        state=state,
        unit_move=unit_move,
        enemy_1=enemy_1,
        enemy_2=enemy_2,
        enemy_3=enemy_3,
    )


def test_no_interrupt(fixture: Fixture) -> None:

    action = WaypointMoveAction(
        unit_id=fixture.unit_move,
        move_to_waypoint_id=1,
    )

    interrupts = fixture.state.get_move_interrupts(
        action.unit_id,
        action.move_to_waypoint_id,
    )

    assert interrupts == [], "Expects no interrupt found at (7, -10)"


def test_one_interrupt(fixture: Fixture) -> None:

    action = WaypointMoveAction(
        unit_id=fixture.unit_move,
        move_to_waypoint_id=2,
    )

    interrupts = fixture.state.get_move_interrupts(
        action.unit_id,
        action.move_to_waypoint_id,
    )

    assert interrupts == [
        (2, [fixture.enemy_1, fixture.enemy_2])
    ], "Expects one interrupt at (7.5, -10) with two enemies"


def test_two_interrupts(fixture: Fixture) -> None:

    action = WaypointMoveAction(
        unit_id=fixture.unit_move,
        move_to_waypoint_id=3,
    )

    interrupts = fixture.state.get_move_interrupts(
        action.unit_id,
        action.move_to_waypoint_id,
    )

    assert interrupts == [
        (2, [fixture.enemy_1, fixture.enemy_2]),
        (3, [fixture.enemy_3]),
    ], "Expects one interrupt at (7.5, -10) with two enemies"


def test_permutations(fixture: Fixture) -> None:
    action = WaypointMoveAction(
        unit_id=fixture.unit_move,
        move_to_waypoint_id=2,
    )
    interrupts = fixture.state.get_move_interrupts(
        action.unit_id,
        action.move_to_waypoint_id,
    )
    _, enemies = interrupts[0]
    fire_permutations = fixture.state.get_all_fire_permutations(enemies)
    total_prob = 0
    for prob, _ in fire_permutations:
        total_prob += prob
    assert total_prob == 1, "Total probability must sum to 1"

    total_prob = 0
    branches = fixture.state.get_branches(action)
    for id, (prob, branch) in enumerate(branches):
        total_prob += prob
        # Unit could be pinned, suppressed, or killed
        # Need to cross reference this with the permutation
        _, fire_event = fire_permutations[id]
        match fire_event:
            case {2: FireOutcomes.PIN, 3: FireOutcomes.PIN}:
                unit = branch.combat_units[fixture.unit_move]
                assert (
                    unit.status == CombatUnit.Status.PINNED
                ), "Expects PIN fire event to result in PINNED status"
            case {2: FireOutcomes.PIN, 3: FireOutcomes.SUPPRESS}:
                unit = branch.combat_units[fixture.unit_move]
                assert (
                    unit.status == CombatUnit.Status.SUPPRESSED
                ), "Expects SUPPRESSED fire event to result in SUPPRESSED status"
            case {2: FireOutcomes.SUPPRESS, 3: FireOutcomes.PIN}:
                unit = branch.combat_units[fixture.unit_move]
                assert (
                    unit.status == CombatUnit.Status.SUPPRESSED
                ), "Expects SUPPRESSED fire event to result in SUPPRESSED status"
            case {2: FireOutcomes.SUPPRESS, 3: FireOutcomes.SUPPRESS}:
                assert (
                    fixture.unit_move not in branch.combat_units
                ), "Expects double SUPPRESSED fire event to kill unit"
            case _:
                ...
    assert total_prob == 1, "Total probability must sum to 1"
