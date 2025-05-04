from dataclasses import dataclass
import pytest
import esper
from core.components import TerrainFeature, UnitCondition, MovementControls, Transform
from core.fire_action import FireAction
from core.vec2 import Vec2


@dataclass
class Fixture:
    attacker_id: int
    target_id: int


@pytest.fixture
def fixture() -> Fixture:
    esper.clear_database()

    # Rifle Squads
    attacker_id = esper.create_entity(
        Transform(position=Vec2(0, -10)), MovementControls(), UnitCondition()
    )
    target_id = esper.create_entity(
        Transform(position=Vec2(15, 20)), MovementControls(), UnitCondition()
    )

    # 10x10 opaque box
    esper.create_entity(
        Transform(position=Vec2(0, 0)),
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
    return Fixture(attacker_id, target_id)


def test_no_fire(fixture: Fixture) -> None:
    FireAction.fire(fixture.attacker_id, fixture.target_id)
    target_status = esper.component_for_entity(fixture.target_id, UnitCondition)
    assert (
        target_status.status == UnitCondition.Status.ACTIVE
    ), "Target target expects to be ACTIVE as it is not shot at"


def test_fire(fixture: Fixture) -> None:
    attacker_transform = esper.component_for_entity(fixture.target_id, Transform)
    attacker_transform.position = Vec2(7.6, -10)
    FireAction.fire(fixture.attacker_id, fixture.target_id)
    target_status = esper.component_for_entity(fixture.target_id, UnitCondition)
    assert (
        target_status.status == UnitCondition.Status.SUPPRESSED
    ), "Target target expects to be SUPPRESSED as it is shot at"
