from dataclasses import dataclass
import math

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem


@dataclass
class Fixture:
    gs: GameState
    unit_move: int
    unit_friendly: int
    unit_shoot: int
    fire_controls: FireControls


@pytest.fixture
def reactive_fixture() -> Fixture:
    gs = GameState()
    # Rifle Squads
    gs.add_entity(InitiativeState())
    unit_move = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -10)),
    )
    unit_friendly = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -11)),
    )
    unit_shoot = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        fire_controls := FireControls(),
        Transform(position=Vec2(15, 20)),
    )
    # orient shooter so that its forward cone contains the moving unit's
    # starting position.  this keeps the various interrupt tests deterministic
    shooter_transform = gs.get_component(unit_shoot, Transform)
    mover_transform = gs.get_component(unit_move, Transform)
    rel = mover_transform.position - shooter_transform.position
    theta = math.degrees(math.atan2(rel.y, rel.x))
    if theta < 0:
        theta += 360
    shooter_transform.degrees = theta

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
        unit_friendly=unit_friendly,
        unit_shoot=unit_shoot,
        fire_controls=fire_controls,
    )


def test_move(reactive_fixture: Fixture) -> None:
    """Basic movement with shooter facing away should see no reactive fire.

    The fixture's setup orients the shooter toward the mover by default, so we
    reset its heading here to an 'away' direction to guarantee no interrupts
    occur in this simple check.  Other tests below restore the 'toward' heading
    via the fixture.
    """
    shooter_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, Transform
    )
    shooter_transform.degrees = 0  # point east, away from mover

    MoveSystem.move(reactive_fixture.gs, reactive_fixture.unit_move, Vec2(5, -15))
    transform = reactive_fixture.gs.get_component(reactive_fixture.unit_move, Transform)
    assert transform.position == Vec2(
        5, -15
    ), "Move action expects to not be interrupted"
    assert (
        InitiativeSystem.has_initiative(
            reactive_fixture.gs, reactive_fixture.unit_shoot
        )
        == False
    ), "NO reactive fire mustn't flip initiative."




def test_reactive_fire_fov_blocks(reactive_fixture: Fixture) -> None:
    """A shooter with clear LOS but pointed away should *not* interrupt.

    This exercise reuses the existing geometry used by the other interrupt
    tests but forces the attacker to look in the opposite direction.  Without
    the new FOV logic in :class:`MoveSystem`, the movement would be interrupted
    and the unit pinned (since we override to PIN).
    """
    reactive_fixture.fire_controls.override = FireOutcomes.PIN
    # point the shooter roughly to the east, which is away from the mover
    shooter_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, Transform
    )
    shooter_transform.degrees = 0

    MoveSystem.move(reactive_fixture.gs, reactive_fixture.unit_move, Vec2(20, -10))
    transform = reactive_fixture.gs.get_component(reactive_fixture.unit_move, Transform)
    assert transform.position == Vec2(
        20, -10
    ), "Move should complete because reactive fire is outside FOV"
    assert (
        InitiativeSystem.has_initiative(
            reactive_fixture.gs, reactive_fixture.unit_shoot
        )
        == False
    ), "FOV block should prevent any initiative flip"


def test_reactive_fire_enters_fov_interrupts() -> None:
    """Reactive fire should trigger once movement enters FOV, not only at start.

    This is a regression for the previous candidate-point approach where only
    one LOS boundary point (or the start point) was checked against FOV.
    """
    gs = GameState()
    gs.add_entity(InitiativeState())

    mover_id = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(-10, 5)),
    )
    shooter_id = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, 0), degrees=0),
    )

    # boundary-only opaque terrain so LOS is broadly available
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

    result = MoveSystem.move(gs, mover_id, Vec2(10, 0))
    assert not isinstance(result, InvalidAction)
    assert result.reactive_fire_outcome == FireOutcomes.PIN

    mover_transform = gs.get_component(mover_id, Transform)
    mover_unit = gs.get_component(mover_id, CombatUnit)
    assert mover_unit.status == CombatUnit.Status.PINNED
    assert mover_transform.position != Vec2(-10, 5)
    assert mover_transform.position != Vec2(10, 0)
    assert InitiativeSystem.has_initiative(gs, shooter_id) == False

def test_interrupt_miss(reactive_fixture: Fixture) -> None:
    # make sure shooter is oriented toward the mover for these interrupt tests
    shooter_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, Transform
    )
    mover_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_move, Transform
    )
    rel = mover_transform.position - shooter_transform.position
    theta = math.degrees(math.atan2(rel.y, rel.x))
    if theta < 0:
        theta += 360
    shooter_transform.degrees = theta
    reactive_fixture.fire_controls.override = FireOutcomes.MISS
    MoveSystem.move(reactive_fixture.gs, reactive_fixture.unit_move, Vec2(20, -10))
    transform = reactive_fixture.gs.get_component(reactive_fixture.unit_move, Transform)
    assert transform.position == Vec2(
        20, -10
    ), "Move action expects to not be interrupted"
    fire_controls = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, FireControls
    )
    assert (
        fire_controls.can_reactive_fire == False
    ), "MISS reactive fire results in NO FIRE"
    assert (
        InitiativeSystem.has_initiative(
            reactive_fixture.gs, reactive_fixture.unit_shoot
        )
        == False
    ), "MISS reactive fire mustn't flip initiative"
    InitiativeSystem.flip_initiative(reactive_fixture.gs)
    assert (
        fire_controls and fire_controls.can_reactive_fire == True
    ), "Passing initiative must reset reactive fire"


def test_interrupt_pin(reactive_fixture: Fixture) -> None:
    shooter_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, Transform
    )
    mover_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_move, Transform
    )
    rel = mover_transform.position - shooter_transform.position
    theta = math.degrees(math.atan2(rel.y, rel.x))
    if theta < 0:
        theta += 360
    shooter_transform.degrees = theta
    reactive_fixture.fire_controls.override = FireOutcomes.PIN
    MoveSystem.move(reactive_fixture.gs, reactive_fixture.unit_move, Vec2(20, -10))
    transform = reactive_fixture.gs.get_component(reactive_fixture.unit_move, Transform)
    assert transform.position == Vec2(
        7.5, -10
    ), "Move action expects to be interrupted at Vec2(7.5, -10)"
    unit = reactive_fixture.gs.get_component(reactive_fixture.unit_move, CombatUnit)
    assert unit.status == CombatUnit.Status.PINNED, "Target expects to be pinned"
    assert (
        InitiativeSystem.has_initiative(
            reactive_fixture.gs, reactive_fixture.unit_shoot
        )
        == False
    ), "PINNED reactive fire must maintain initiative."
    assert (
        reactive_fixture.fire_controls.can_reactive_fire == True
    ), "PINNED reactive fire doesn't mark shooter as NO FIRE"


def test_interrupt_suppress(reactive_fixture: Fixture) -> None:
    shooter_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, Transform
    )
    mover_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_move, Transform
    )
    rel = mover_transform.position - shooter_transform.position
    theta = math.degrees(math.atan2(rel.y, rel.x))
    if theta < 0:
        theta += 360
    shooter_transform.degrees = theta
    reactive_fixture.fire_controls.override = FireOutcomes.SUPPRESS
    MoveSystem.move(reactive_fixture.gs, reactive_fixture.unit_move, Vec2(20, -10))
    transform = reactive_fixture.gs.get_component(reactive_fixture.unit_move, Transform)
    assert transform.position == Vec2(
        7.5, -10
    ), "Move action expects to be interrupted at Vec2(8, -10)"
    unit = reactive_fixture.gs.get_component(reactive_fixture.unit_move, CombatUnit)
    assert (
        unit.status == CombatUnit.Status.SUPPRESSED
    ), "Target expects to be suppressed"
    assert (
        InitiativeSystem.has_initiative(
            reactive_fixture.gs, reactive_fixture.unit_shoot
        ) == True
    ), "SUPPRESS reactive fire must flip initiative."


def test_interrupt_kill(reactive_fixture: Fixture) -> None:
    shooter_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_shoot, Transform
    )
    mover_transform = reactive_fixture.gs.get_component(
        reactive_fixture.unit_move, Transform
    )
    rel = mover_transform.position - shooter_transform.position
    theta = math.degrees(math.atan2(rel.y, rel.x))
    if theta < 0:
        theta += 360
    shooter_transform.degrees = theta
    reactive_fixture.fire_controls.override = FireOutcomes.KILL
    MoveSystem.move(reactive_fixture.gs, reactive_fixture.unit_move, Vec2(20, -10))
    transform = reactive_fixture.gs.try_component(reactive_fixture.unit_move, Transform)
    assert transform == None, "Target expects to be killed"
    assert (
        InitiativeSystem.has_initiative(
            reactive_fixture.gs, reactive_fixture.unit_shoot
        ) == True
    ), "KILL reactive fire must flip initiative"
