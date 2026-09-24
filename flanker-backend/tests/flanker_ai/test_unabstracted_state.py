from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import pytest
from flanker_ai.ai_agent_factory import AiAgentFactory
from flanker_ai.ai_search_agent import AiSearchAgent
from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    PolicyConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
)
from flanker_ai.i_ai_agent import AiActionResult, IAiAgent
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.actions import FireAction, MoveAction
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    MapBoundary,
    MoveControls,
    StallLoseCondition,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    friendly_1: UUID
    friendly_2: UUID
    enemy_1: UUID
    enemy_2: UUID


@pytest.fixture
def fixture() -> Fixture:

    gs = GameState()
    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
    )
    friendly_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            status=CombatUnit.Status.ACTIVE,
        ),
        Transform(position=Vec2(-1, 12), degrees=-90),
        # TODO: should there be a dedicated test for no-fov?
        # Alternatively, perhaps I should refactor all tests to only use no-fov,
        # since the no-fov would be the only case I'd continue with.
        FireControls(
            fov_degrees=90,
            override=FireOutcomes.PIN,
        ),
        AssaultControls(),
    )
    friendly_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            status=CombatUnit.Status.ACTIVE,
        ),
        Transform(position=Vec2(1, 12), degrees=-90),
        FireControls(
            fov_degrees=90,
            override=FireOutcomes.PIN,
        ),
        AssaultControls(),
    )
    enemy_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(
            faction=InitiativeState.Faction.RED,
            status=CombatUnit.Status.ACTIVE,
        ),
        FireControls(
            fov_degrees=90,
            override=FireOutcomes.PIN,
        ),
        Transform(position=Vec2(0, -15), degrees=70),
        AssaultControls(),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(
            faction=InitiativeState.Faction.RED,
            status=CombatUnit.Status.ACTIVE,
        ),
        FireControls(
            fov_degrees=90,
            override=FireOutcomes.PIN,
        ),
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
        MapBoundary(
            vertices=[
                Vec2(-20, -20),
                Vec2(20, -20),
                Vec2(20, 20),
                Vec2(-20, 20),
            ],
        ),
    )

    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        )
    )
    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        )
    )
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            stall_count=0,
            stall_limit=5,
        )
    )
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            stall_count=0,
            stall_limit=5,
        )
    )

    return Fixture(
        gs=gs,
        friendly_1=friendly_1,
        friendly_2=friendly_2,
        enemy_1=enemy_1,
        enemy_2=enemy_2,
    )


def get_agent(
    gs: GameState,
    policy_type: Literal["Minimax", "MCTS"],
) -> IAiAgent[Any]:

    move_candidate_points = [
        Vec2(0, 0),
        Vec2(-10, 1),
        Vec2(-10, 10),
        # Vec2(10, 10),   # These are also optimal peeking nodes
        # Vec2(10, 1),   # but mirrored on the other side
    ]

    match policy_type:
        case "MCTS":
            policy = PolicyConfig.MctsPolicy(
                type="MctsPolicy",
                max_iterations=200,
                max_simulate_length=20,
                simulation_policy="rh",
            )
        case "Minimax":
            policy = PolicyConfig.MinimaxPolicy(
                type="MinimaxPolicy",
                depth=4,
            )

    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.BLUE,
            config=SearchPolicyConfig(
                policy=policy,
                state=UnabstractedStateConfig(
                    type="UnabstractedStateConfig",
                    move_candidates_pool=PointsConfig.HandDrawn(
                        type="HandDrawnConfig",
                        points=move_candidate_points,
                    ),
                    move_candidates_filter=[],
                ),
            ),
        ),
    )

    agent = AiAgentFactory.get_agent(gs, faction=InitiativeState.Faction.BLUE)
    return agent


def test_branching_total_prob(fixture: Fixture) -> None:
    action = MoveAction(
        unit_id=fixture.friendly_1,
        to=Vec2(-10, 1),
    )
    blue_agent = get_agent(fixture.gs, policy_type="Minimax")
    assert isinstance(blue_agent, AiSearchAgent), "BLUE agent must be a search agent"
    blue_agent.rs.update_state(fixture.gs)
    branches = blue_agent.rs.get_branches(action)
    total_prob = 0
    for prob, _ in branches:
        total_prob += prob
    assert total_prob == 1, "Total probability must equal 1"


@pytest.mark.parametrize("policy_type", ["Minimax", "MCTS"])
def test_optimal_actions(
    fixture: Fixture,
    policy_type: Literal["Minimax", "MCTS"],
) -> None:

    blue_agent = get_agent(fixture.gs, policy_type)
    action_results: list[AiActionResult[AiSearchLog]] = []
    for _ in range(10):
        result = blue_agent.perform_action(fixture.gs)
        if result == None:
            break
        action_results.append(result)

    assert action_results != [], "The minimax must find optimal action sequence."

    staging_units: list[UUID] = []
    for result in action_results:
        if not isinstance(result.action, MoveAction):
            continue
        if result.action.to == Vec2(-10, 10):
            staging_units.append(result.action.unit_id)
    assert len(staging_units) != 0, "AI must try staging to Vec2(-10, 10)."

    peeking_units: list[UUID] = []
    for result in action_results:
        if not isinstance(result.action, MoveAction):
            continue
        if result.action.to == Vec2(-10, 1):
            peeking_units.append(result.action.unit_id)
    assert len(peeking_units) != 0, "AI must try peeking to Vec2(-10, 1)."

    assert (
        len(set(peeking_units) & set(staging_units)) != 0
    ), "Peeking units must be staged first."

    last_action_result = action_results[-1]
    assert isinstance(
        last_action_result.action, FireAction
    ), "AI must fire at the enemy once."
