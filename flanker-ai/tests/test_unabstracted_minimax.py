from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_ai.actions import FireActionResult, MoveAction, MoveActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import (
    PointsConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
)
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    FireControls,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeState
from flanker_core.systems.register_systems import register_systems


@dataclass
class Fixture:
    gs: GameState
    blue_agent: AiAgent
    friendly_1: UUID
    friendly_2: UUID
    enemy_1: UUID
    enemy_2: UUID


@pytest.fixture
def fixture() -> Fixture:

    gs = GameState()
    register_systems(gs)
    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
    )
    friendly_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(-1, 12), degrees=-90),
        FireControls(override=FireOutcomes.PIN),
        AssaultControls(),
    )
    friendly_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(1, 12), degrees=-90),
        FireControls(override=FireOutcomes.PIN),
        AssaultControls(),
    )
    enemy_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, -15), degrees=70),
        AssaultControls(),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, -18), degrees=100),
        AssaultControls(),
    )

    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-5, -5),
                Vec2(5, -5),
                Vec2(5, 5),
                Vec2(-5, 5),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )
    # 40x40 boundary
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-20, -20),
                Vec2(20, -20),
                Vec2(20, 20),
                Vec2(-20, 20),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    move_candidate_points = [
        Vec2(0, 0),
        Vec2(-10, 1),
        Vec2(-10, 10),
        # Vec2(10, 10),   # These are also optimal peeking nodes
        # Vec2(10, 1),   # but mirrored on the other side
    ]

    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.BLUE,
            config=SearchPolicyConfig(
                policy_type="Minimax",
                state=UnabstractedStateConfig(
                    type="UnabstractedStateConfig",
                    move_candidates=PointsConfig(
                        initial_points=PointsConfig.HandDrawnConfig(
                            type="HandDrawnConfig",
                            points=move_candidate_points,
                        ),
                        use_combat_unit_positions=False,
                        expansions=[],
                    ),
                    divide_moves_per_unit=False,
                ),
            ),
        )
    )

    blue_agent = AiAgent.get_agent(gs, faction=InitiativeState.Faction.BLUE)

    return Fixture(
        gs=gs,
        blue_agent=blue_agent,
        friendly_1=friendly_1,
        friendly_2=friendly_2,
        enemy_1=enemy_1,
        enemy_2=enemy_2,
    )


def test_stall(fixture: Fixture) -> None:
    agent = fixture.blue_agent
    rs = agent.rs
    assert isinstance(
        rs, UnabstractedState
    ), "Configured agent's state representation must be unabstracted state."
    rs.update_state(fixture.gs)

    # Have it move repeatedly to the same coordinates
    transform = fixture.gs.get_component(fixture.friendly_1, Transform)
    for _ in range(5):
        action = MoveAction(
            unit_id=fixture.friendly_1,
            to=transform.position,
        )
        _, new_state = rs.get_branches(action)[0]
        assert new_state != None, "Actions are not invalid"
        rs = new_state
    assert rs.get_winner() == None, "BLUE must not stall yet."

    action = MoveAction(
        unit_id=fixture.friendly_1,
        to=transform.position,
    )
    _, new_state = rs.get_branches(action)[0]
    assert new_state != None, "Actions are not invalid"
    rs = new_state
    assert (
        rs.get_winner() == InitiativeState.Faction.RED
    ), "BLUE must be considered stall."


def test_branching_total_prob(fixture: Fixture) -> None:
    action = MoveAction(
        unit_id=fixture.friendly_1,
        to=Vec2(-10, 1),
    )
    branches = fixture.blue_agent.rs.get_branches(action)
    total_prob = 0
    for prob, _ in branches:
        total_prob += prob
    assert total_prob == 1, "Total probability must equal 1"


def test_optimal_actions(fixture: Fixture) -> None:
    actions = fixture.blue_agent.play_initiative()
    assert actions != [], "The minimax must find optimal action sequence."
    assert isinstance(
        actions[0], MoveActionResult
    ), "AI must start first with Move Action"
    assert isinstance(
        actions[1], MoveActionResult
    ), "AI must continue with Move Actions"
    assert actions[0].action.to == Vec2(
        -10, 10
    ), "AI must try to peek to the left at Vec2(-10, 10)"
    assert actions[1].action.to == Vec2(
        -10, 1
    ), "AI must try to peek to the left at Vec2(-10, 1)"
    assert isinstance(
        actions[2], FireActionResult
    ), "AI must perform Fire Action after peeking"
