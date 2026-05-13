from dataclasses import dataclass
from math import isclose
from uuid import UUID

import pytest
from flanker_ai.actions import MoveAction
from flanker_ai.states.unabstracted.ai_branching_system import AiBranchingSystem
from flanker_ai.states.waypoints.waypoints_graph_system import WaypointGraphSystem
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
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
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.register_systems import register_systems


@dataclass
class Fixture:
    state: WaypointsState
    unit_move: UUID
    enemy_1: UUID
    enemy_2: UUID
    enemy_3: UUID
    waypoint_positions: list[Vec2]


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    register_systems(gs)
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
        Transform(position=Vec2(15, 20), degrees=-90),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(15, 20), degrees=-90),
    )
    # Have another enemy unit for a second reactive fire
    enemy_3 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(10, 20), degrees=-90),
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

    waypoint_positions = [
        Vec2(6, -10),  # 0
        Vec2(7, -10),  # 1
        Vec2(8, -10),  # 2
        Vec2(20, -10),  # 3
        # The unit positions would be separate indices
    ]

    state = WaypointsState(
        points=waypoint_positions,
        path_tolerance=20,
        is_deterministic=False,
    )

    state.update_state(gs)

    return Fixture(
        state=state,
        unit_move=unit_move,
        enemy_1=enemy_1,
        enemy_2=enemy_2,
        enemy_3=enemy_3,
        waypoint_positions=waypoint_positions,
    )


def test_no_interrupt(fixture: Fixture) -> None:
    move_system = fixture.state.gs.get(MoveSystem)

    move_position = fixture.waypoint_positions[1]
    action = MoveAction(
        unit_id=fixture.unit_move,
        to=move_position,
    )
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=action.unit_id,
        to=move_position,
    )

    assert interrupts == [], "Expects no interrupt found at (7, -10)"


def test_one_interrupt(fixture: Fixture) -> None:
    move_system = fixture.state.gs.get(MoveSystem)
    waypoints_system = fixture.state.gs.get(WaypointGraphSystem)

    move_position = fixture.waypoint_positions[2]
    action = MoveAction(
        unit_id=fixture.unit_move,
        to=move_position,
    )
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=action.unit_id,
        to=move_position,
    )

    waypoints = waypoints_system.get_waypoints(fixture.state.gs)
    assert interrupts == [
        (waypoints[2].position, [fixture.enemy_1, fixture.enemy_2])
    ], "Expects one interrupt at (7.5, -10) with two enemies"


def test_two_interrupts(fixture: Fixture) -> None:
    move_system = fixture.state.gs.get(MoveSystem)
    waypoints_system = fixture.state.gs.get(WaypointGraphSystem)

    move_position = fixture.waypoint_positions[3]
    action = MoveAction(
        unit_id=fixture.unit_move,
        to=move_position,
    )
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=action.unit_id,
        to=move_position,
    )

    waypoints = waypoints_system.get_waypoints(fixture.state.gs)
    assert interrupts == [
        (waypoints[2].position, [fixture.enemy_1, fixture.enemy_2]),
        (waypoints[3].position, [fixture.enemy_3]),
    ], "Expects one interrupt at (7.5, -10) with two enemies"


def test_reactive_fire_permutations(fixture: Fixture) -> None:
    move_system = fixture.state.gs.get(MoveSystem)
    branching_system = fixture.state.gs.get(AiBranchingSystem)
    move_position = fixture.waypoint_positions[2]
    action = MoveAction(
        unit_id=fixture.unit_move,
        to=move_position,
    )
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=action.unit_id,
        to=move_position,
    )
    _, enemies = interrupts[0]
    fire_permutations = branching_system.get_permutations(
        unit_ids=set(enemies),
        outcome_probabilities={
            FireOutcomes.PIN: 0.6,
            FireOutcomes.SUPPRESS: 0.4,
        },
    )
    total_prob = 0
    for prob, _ in fire_permutations:
        total_prob += prob
    assert isclose(total_prob, 1), "Total probability must sum to 1"

    branches = fixture.state.get_branches(action)
    for id, (prob, branch) in enumerate(branches):
        # Unit could be pinned, suppressed, or killed
        # Need to cross reference this with the permutation
        _, fire_event = fire_permutations[id]
        match fire_event:
            # I hate this test case
            case {
                fixture.enemy_1: FireOutcomes.PIN,
                fixture.enemy_2: FireOutcomes.PIN,
            }:
                unit = branch.gs.get_component(fixture.unit_move, CombatUnit)
                assert (
                    unit.status == CombatUnit.Status.PINNED
                ), "Expects PIN fire event to result in PINNED status"
                assert (
                    branch.get_initiative() == InitiativeState.Faction.BLUE
                ), "Expects PIN fire event to not flip initiative."
            case {
                fixture.enemy_1: FireOutcomes.PIN,
                fixture.enemy_2: FireOutcomes.SUPPRESS,
            }:
                unit = branch.gs.get_component(fixture.unit_move, CombatUnit)
                assert (
                    unit.status == CombatUnit.Status.SUPPRESSED
                ), "Expects SUPPRESS fire event to result in SUPPRESSED status"
                assert (
                    branch.get_initiative() == InitiativeState.Faction.RED
                ), "Expects SUPPRESS fire event to flip initiative."
            case {
                fixture.enemy_1: FireOutcomes.SUPPRESS,
                fixture.enemy_2: FireOutcomes.PIN,
            }:
                unit = branch.gs.get_component(fixture.unit_move, CombatUnit)
                assert (
                    unit.status == CombatUnit.Status.SUPPRESSED
                ), "Expects SUPPRESS fire event to result in SUPPRESSED status"
                assert (
                    branch.get_initiative() == InitiativeState.Faction.RED
                ), "Expects SUPPRESS fire event to flip initiative."
            case {
                fixture.enemy_1: FireOutcomes.SUPPRESS,
                fixture.enemy_2: FireOutcomes.SUPPRESS,
            }:
                assert (
                    branch.gs.try_component(fixture.unit_move, CombatUnit) == None
                ), "Expects double SUPPRESS fire event to kill unit"
                assert (
                    branch.get_initiative() == InitiativeState.Faction.RED
                ), "Expects double SUPPRESS fire event to flip initiative."
            case _:
                ...
