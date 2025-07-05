from dataclasses import dataclass
import pytest

from core.components import CommandUnit, MoveControls, TerrainFeature, CombatUnit
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


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    cmd1 = gs.add_entity(CommandUnit(has_initiative=True))
    cmd2 = gs.add_entity(CommandUnit(has_initiative=False))
    unit_move = gs.add_entity(
        MoveControls(), CombatUnit(command_id=cmd1), Transform(position=Vec2(0, -10))
    )
    unit_friendly = gs.add_entity(
        MoveControls(), CombatUnit(command_id=cmd1), Transform(position=Vec2(0, -11))
    )
    unit_shoot = gs.add_entity(
        MoveControls(), CombatUnit(command_id=cmd2), Transform(position=Vec2(15, 20))
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
        gs=gs, unit_move=unit_move, unit_friendly=unit_friendly, unit_shoot=unit_shoot
    )


def test_move(fixture: Fixture) -> None:
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform and (
        transform.position == Vec2(5, -15)
    ), "Move action expects to not be interrupted"


def test_los_interrupt(fixture: Fixture) -> None:
    MoveAction.move(fixture.gs, fixture.unit_move, Vec2(20, -10))
    transform = fixture.gs.get_component(fixture.unit_move, Transform)
    assert transform and (
        transform.position == Vec2(8, -10)
    ), "Move action expects to be interrupted at Vec2(7.6, -10)"
    unit = fixture.gs.get_component(fixture.unit_move, CombatUnit)
    assert unit and (
        unit.status == CombatUnit.status.SUPPRESSED
    ), "Target expects to be suppressed"
