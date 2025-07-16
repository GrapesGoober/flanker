from dataclasses import dataclass
import pytest

from backend import Command
from core.components import (
    Faction,
    FireControls,
    MoveControls,
    TerrainFeature,
    CombatUnit,
)
from core.gamestate import GameState
from core.los_check import Transform
from core.move_action import MoveAction
from core.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    unit_move: int
    unit_friendly: int
    unit_shoot: int
    fire_controls: FireControls
    hostile_faction: Faction


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    friendly_faction_id = gs.add_entity(
        Faction(has_initiative=True),
    )
    hostile_faction_id = gs.add_entity(
        faction := Faction(has_initiative=False),
    )
    unit_move = gs.add_entity(
        MoveControls(),
        CombatUnit(command_id=friendly_faction_id),
        Transform(position=Vec2(0, -10)),
    )
    unit_friendly = gs.add_entity(
        MoveControls(),
        CombatUnit(command_id=friendly_faction_id),
        Transform(position=Vec2(0, -11)),
    )
    unit_shoot = gs.add_entity(
        MoveControls(),
        CombatUnit(command_id=hostile_faction_id),
        fire_controls := FireControls(),
        Transform(position=Vec2(15, 20)),
    )

    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), angle=0),
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

    return Fixture(
        gs=gs,
        unit_move=unit_move,
        unit_friendly=unit_friendly,
        unit_shoot=unit_shoot,
        fire_controls=fire_controls,
        hostile_faction=faction,
    )


def test_move(fixture: Fixture) -> None:
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform and (
        transform.position == Vec2(5, -15)
    ), "Move action expects to not be interrupted"
    assert (
        fixture.hostile_faction.has_initiative == False
    ), "NO reactive fire mustn't flip initiative."


def test_interrupt_miss(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.MISS
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform and (
        transform.position == Vec2(20, -10)
    ), "Move action expects to not be interrupted"
    fire_controls = fixture.gs.get_component(fixture.unit_shoot, FireControls)
    assert (
        fire_controls and fire_controls.can_reactive_fire == False
    ), "MISS reactive fire results in NO FIRE"
    assert (
        fixture.hostile_faction.has_initiative == False
    ), "MISS reactive fire mustn't flip initiative"
    Command.flip_initiative(fixture.gs)
    assert (
        fire_controls and fire_controls.can_reactive_fire == True
    ), "Passing initiative must reset reactive fire"


def test_interrupt_pin(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.PIN
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform and (
        transform.position == Vec2(8, -10)
    ), "Move action expects to be interrupted at Vec2(8, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert unit and (
        unit.status == CombatUnit.status.PINNED
    ), "Target expects to be pinned"
    assert (
        fixture.hostile_faction.has_initiative == False
    ), "PINNED reactive fire must maintain initiative."
    assert (
        fixture.fire_controls.can_reactive_fire == True
    ), "PINNED reactive fire doesn't mark shooter as NO FIRE"


def test_interrupt_suppress(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.SUPPRESS
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform and (
        transform.position == Vec2(8, -10)
    ), "Move action expects to be interrupted at Vec2(8, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert unit and (
        unit.status == CombatUnit.status.SUPPRESSED
    ), "Target expects to be suppressed"
    assert (
        fixture.hostile_faction.has_initiative == True
    ), "SUPPRESS reactive fire must flip initiative."


def test_interrupt_kill(fixture: Fixture) -> None:
    fixture.fire_controls.override = FireControls.Outcomes.KILL
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform == None, "Target expects to be killed"
    assert (
        fixture.hostile_faction.has_initiative == True
    ), "KILL reactive fire must flip initiative"
