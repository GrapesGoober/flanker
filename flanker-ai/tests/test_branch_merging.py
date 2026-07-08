from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_ai.states.common.ai_branch_abstraction_service import (
    AiBranchAbstractionService,
)
from flanker_ai.states.common.ai_branching_service import AiBranchingService
from flanker_core.gamestate import GameState
from flanker_core.models.actions import MoveAction
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeState
from flanker_core.systems.move_system import MoveSystem


@dataclass
class Fixture:
    gs: GameState
    unit_move: UUID
    enemy_1: UUID
    enemy_2: UUID


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
        Transform(position=Vec2(15, 20), degrees=-90),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(),
        Transform(position=Vec2(15, 20), degrees=-90),
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

    return Fixture(
        gs=gs,
        unit_move=unit_move,
        enemy_1=enemy_1,
        enemy_2=enemy_2,
    )


def test_copy(fixture: Fixture) -> None:
    new_gs = AiBranchingService.copy(fixture.gs)

    # Check that combat units are copied
    for unit_id, unit, transform, fire_controls in new_gs.query(
        CombatUnit, Transform, FireControls
    ):
        old_unit = fixture.gs.get_component(unit_id, CombatUnit)
        old_transform = fixture.gs.get_component(unit_id, Transform)
        old_fire_controls = fixture.gs.get_component(unit_id, FireControls)

        assert id(old_unit) != id(unit)
        assert id(old_transform) != id(transform)
        assert id(old_fire_controls) != id(fire_controls)

    # Check that terrains are not copied
    for terrain_id, transform, terrain in new_gs.query(Transform, TerrainFeature):
        old_transform = fixture.gs.get_component(terrain_id, Transform)
        old_terrain = fixture.gs.get_component(terrain_id, TerrainFeature)

        assert id(old_transform) != id(transform)
        assert id(old_terrain) == id(terrain)


def test_one_interrupt(fixture: Fixture) -> None:
    move_position = Vec2(20, -10)
    interrupts = MoveSystem.get_interrupt_candidates(
        gs=fixture.gs,
        unit_id=fixture.unit_move,
        to=move_position,
    )

    assert len(interrupts) == 1, "There must be only 1 interrupt"
    assert len(interrupts[0][1]) == 2, "There must be two enemies"


def test_branches(fixture: Fixture) -> None:

    move_action = MoveAction(
        unit_id=fixture.unit_move,
        to=Vec2(20, -10),
    )

    branches = AiBranchingService.get_action_branches(
        gs=fixture.gs,
        action=move_action,
    )
    total_probability = 0
    for probability, _ in branches:
        total_probability += probability
    assert total_probability == 1, "The total probability must be 1"

    merged_branches = AiBranchAbstractionService.merge_branches(
        branches=branches,
        action=move_action,
    )

    total_probability = 0
    for probability, _ in merged_branches:
        total_probability += probability
    assert total_probability == 1, "The total probability must be 1"

    assert len(merged_branches) < len(
        branches
    ), "The merged branches must be smaller than original branches"
