from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.actions import RallyAction
from flanker_core.models.components import (
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    RallyStallLoseCondition,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class Fixture:
    gs: GameState
    blue_unit_id: UUID
    red_unit_id: UUID


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(
        InitiativeState(),
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        ),
    )
    gs.add_entity(
        RallyStallLoseCondition(
            rally_stall_count=0,
            rally_stall_limit=2,
            last_rallied_faction=None,
        ),
    )
    blue_unit_id = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            status=CombatUnit.Status.ACTIVE,
        ),
        FireControls(
            override=FireOutcomes.KILL,
            fov_degrees=90,
        ),
        Transform(position=Vec2(0, 0)),
    )
    red_unit_id = gs.add_entity(
        CombatUnit(
            faction=InitiativeState.Faction.RED,
            status=CombatUnit.Status.ACTIVE,
        ),
        Transform(position=Vec2(2, 1)),
    )

    return Fixture(
        gs=gs,
        blue_unit_id=blue_unit_id,
        red_unit_id=red_unit_id,
    )


def test_rally(fixture: Fixture) -> None:

    assert (
        ActionSystem.get_initiative(fixture.gs) == InitiativeState.Faction.BLUE
    ), "Expects initiative to start with BLUE."

    unit = fixture.gs.get_component(fixture.blue_unit_id, CombatUnit)
    unit.status = CombatUnit.Status.PINNED

    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.blue_unit_id,
        ),
    )

    assert (
        unit.status == CombatUnit.Status.ACTIVE
    ), "Expects unit status to recover to ACTIVE."

    assert (
        ActionSystem.get_initiative(fixture.gs) == InitiativeState.Faction.RED
    ), "Expects initiative to flip to RED."


def test_rally_stalls(fixture: Fixture) -> None:
    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.blue_unit_id,
        ),
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as stalls not met"

    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.red_unit_id,
        ),
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as stalls not met"

    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.blue_unit_id,
        ),
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert (
        winner == InitiativeState.Faction.RED
    ), "Expects RED to win as BLUE performs the last stalling rally."


def test_rally_stalls_resets(fixture: Fixture) -> None:
    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.blue_unit_id,
        ),
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as stalls not met"

    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.red_unit_id,
        ),
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects no winner as stalls not met"

    # Make this unit pinned, so that its rally is not considered stalling
    unit = fixture.gs.get_component(fixture.blue_unit_id, CombatUnit)
    unit.status = CombatUnit.Status.PINNED

    _ = ActionSystem.perform(
        gs=fixture.gs,
        action=RallyAction(
            unit_id=fixture.blue_unit_id,
        ),
    )
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert (
        winner == None
    ), "Expects no winner since rally is not stalling and resets counter."
