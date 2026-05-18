from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_ai.actions import MoveAction
from flanker_ai.states.common.ai_branch_abstraction_service import (
    AiBranchAbstractionService,
)
from flanker_ai.states.common.ai_branching_service import AiBranchingService
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
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=fixture.unit_move,
        to=move_position,
    )

    assert interrupts == [], "Expects no interrupt found at (7, -10)"


def test_one_interrupt(fixture: Fixture) -> None:
    move_system = fixture.state.gs.get(MoveSystem)

    move_position = fixture.waypoint_positions[2]
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=fixture.unit_move,
        to=move_position,
    )
    assert interrupts == [
        (fixture.waypoint_positions[2], [fixture.enemy_1, fixture.enemy_2])
    ], "Expects one interrupt with two enemies"


def test_two_interrupts(fixture: Fixture) -> None:
    move_system = fixture.state.gs.get(MoveSystem)

    move_position = fixture.waypoint_positions[3]
    interrupts = move_system.get_interrupt_candidates(
        gs=fixture.state.gs,
        unit_id=fixture.unit_move,
        to=move_position,
    )

    assert interrupts == [
        (fixture.waypoint_positions[2], [fixture.enemy_1, fixture.enemy_2]),
        (fixture.waypoint_positions[3], [fixture.enemy_3]),
    ], "Expects two interrupts with three enemies"


def test_reactive_fire_branches(fixture: Fixture) -> None:
    # Based on test_one_interrupt, there are two enemies reactive fire
    permutations = AiBranchingService.get_permutations(
        unit_ids={fixture.enemy_1, fixture.enemy_2},
        outcome_probabilities={
            FireOutcomes.PIN: 0.6,
            FireOutcomes.SUPPRESS: 0.4,
        },
    )

    # Check that the configured branch matches the permutations
    move_position = fixture.waypoint_positions[2]
    branches = AiBranchingService.get_reactive_fire_branches(
        gs=fixture.state.gs,
        unit_id=fixture.unit_move,
        move_to=move_position,
    )
    for probability, branch in branches:
        enemy_1_fire = branch.get_component(fixture.enemy_1, FireControls)
        enemy_2_fire = branch.get_component(fixture.enemy_2, FireControls)
        assert (
            probability,
            {
                fixture.enemy_1: enemy_1_fire.override,
                fixture.enemy_2: enemy_2_fire.override,
            },
        ) in permutations


def test_deterministic_double_pin(fixture: Fixture) -> None:
    # Based on test_one_interrupt, there are two enemies reactive fire.
    # Thus the most likely outcome is being suppressed.

    move_position = fixture.waypoint_positions[2]
    move_action = MoveAction(unit_id=fixture.unit_move, to=move_position)

    branches = AiBranchingService.get_action_branches(
        gs=fixture.state.gs,
        action=move_action,
    )
    branch = AiBranchAbstractionService.pick_branch(
        branches=branches,
        action=move_action,
    )

    enemy_1_fire = branch.get_component(fixture.enemy_1, FireControls)
    enemy_2_fire = branch.get_component(fixture.enemy_2, FireControls)

    assert set([enemy_1_fire.override, enemy_2_fire.override]) == {
        FireOutcomes.PIN,
        FireOutcomes.SUPPRESS,
    }, "At least one reactive fire must SUPPRESS, the other PIN."
