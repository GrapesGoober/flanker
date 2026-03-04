import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, InitiativeState, Transform, FireControls
from flanker_core.models.outcomes import InvalidAction, FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.pivot_system import PivotSystem


class Fixture:
    def __init__(self):
        self.gs = GameState()
        # add initiative manager with BLUE
        self.gs.add_entity(InitiativeState())
        # create a single friendly squad at origin
        self.unit_id = self.gs.add_entity(
            CombatUnit(faction=InitiativeState.Faction.BLUE),
            Transform(position=Vec2(0, 0), degrees=0),
        )


@pytest.fixture
def fixture() -> Fixture:
    return Fixture()


# pylint: disable=redefined-outer-name

def test_pivot_changes_degrees(fixture: Fixture) -> None:
    # ensure pivot occurs when unit has initiative and is active
    result = PivotSystem.pivot(fx.gs, fx.unit_id, 123.4)
    assert not isinstance(result, InvalidAction)
    transform = fx.gs.get_component(fx.unit_id, Transform)
    assert transform.degrees == 123.4
    # pivot should be normalized
    result2 = PivotSystem.pivot(fx.gs, fx.unit_id, 400)
    assert not isinstance(result2, InvalidAction)
    assert fx.gs.get_component(fx.unit_id, Transform).degrees == 40.0
    # initiative is not flipped
    assert InitiativeSystem.has_initiative(fx.gs, fx.unit_id)


# pylint: disable=redefined-outer-name

def test_pivot_no_initiative(fixture: Fixture) -> None:
    # set initiative to opposing faction
    InitiativeSystem.set_initiative(fx.gs, InitiativeState.Faction.RED)
    reason = PivotSystem.pivot(fx.gs, fx.unit_id, 50)
    assert reason == InvalidAction.NO_INITIATIVE


# pylint: disable=redefined-outer-name

def test_pivot_inactive_status(fixture: Fixture) -> None:
    # suppressed units cannot pivot
    unit = fx.gs.get_component(fx.unit_id, CombatUnit)
    unit.status = CombatUnit.Status.SUPPRESSED
    reason = PivotSystem.pivot(fx.gs, fx.unit_id, 75)
    assert reason == InvalidAction.INACTIVE_UNIT

    # pinned units are allowed
    unit.status = CombatUnit.Status.PINNED
    result = PivotSystem.pivot(fx.gs, fx.unit_id, 75)
    assert not isinstance(result, InvalidAction)


# pylint: disable=redefined-outer-name

def test_pivot_reactive_fire(fixture: Fixture) -> None:
    # add a spotter that can reactively fire on the pivoting unit
    _spotter_id = fx.gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(1, 0)),
    )
    # ensure blue unit has initiative and is in LOS of spotter (no terrain)
    InitiativeSystem.set_initiative(fx.gs, InitiativeState.Faction.BLUE)
    # perform pivot; reactive fire should pin the unit
    result = PivotSystem.pivot(fx.gs, fx.unit_id, 180)
    assert not isinstance(result, InvalidAction)
    unit = fx.gs.get_component(fx.unit_id, CombatUnit)
    assert unit.status == CombatUnit.Status.PINNED, "Pivot should trigger pin from reactive fire"

