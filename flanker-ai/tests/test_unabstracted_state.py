import random

import pytest
from flanker_ai.actions import PivotAction
from flanker_ai.components import AiStallCountComponent
from flanker_ai.states.unabstracted_state import UnabstractedState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    Transform,
    FireControls,
    TerrainFeature,
)
from flanker_core.models.vec2 import Vec2


@pytest.fixture(autouse=True)
def seed_random():
    # keep test deterministic when random sampling is used
    random.seed(12345)


def make_simple_gs() -> GameState:
    gs = GameState()
    # initiative component (singleton)
    gs.add_entity(InitiativeState(faction=InitiativeState.Faction.BLUE))

    # include a simple boundary so bounds computation succeeds
    gs.add_entity(
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
            ],
            is_closed_loop=True,
            flag=TerrainFeature.Flag.BOUNDARY,
        ),
        Transform(position=Vec2(0, 0)),
    )

    # create a single blue combat unit with a transform and fire controls
    eid = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, 0), degrees=0),
        FireControls(),
    )
    # add stall counter component (used by unabstracted state)
    gs.add_entity(AiStallCountComponent())
    return gs


def test_pivot_action_generated() -> None:
    gs = make_simple_gs()
    state = UnabstractedState(gs)
    actions = state.get_actions()
    assert any(isinstance(a, PivotAction) for a in actions)


def test_pivot_branch_applies() -> None:
    gs = make_simple_gs()
    state = UnabstractedState(gs)
    actions = state.get_actions()
    pivot_actions = [a for a in actions if isinstance(a, PivotAction)]
    assert pivot_actions, "no pivot actions generated"
    action = pivot_actions[0]
    new_state = state.get_deterministic_branch(action)
    assert new_state is not None
    # verify orientation updated
    eid = next(unit_id for unit_id, _ in gs.query(CombatUnit))
    deg = new_state._gs.get_component(eid, Transform).degrees
    assert deg == action.degrees % 360
