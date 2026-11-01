import random
from copy import deepcopy
from dataclasses import dataclass
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path

from flanker_ai.agents.ai_search_agent import AiSearchAgent
from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    PolicyConfig,
    SearchPolicyConfig,
    TranspositionScheme,
    UnabstractedStateConfig,
)
from flanker_ai.search_policies.minimax_policy import MinimaxPolicy
from flanker_ai.search_states.common.ai_transposition_key_service import (
    AiTranspositionKeyService,
    CacheKey,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    MapBoundary,
    MoveControls,
    RallyStallLoseCondition,
    StallLoseCondition,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from pydantic import BaseModel
from transposition_experiment_models import TranspositionExperimentSetConfig


@dataclass(frozen=True)
class AiTreeResult:
    best_action: Action | None
    value: float


@dataclass(frozen=True)
class TranspositionTestRun:
    same_states: bool


class TranspositionTestResult(BaseModel):
    same_states: bool
    key_is_same: bool
    result_is_same: bool


def main() -> None:
    results_path = Path(
        "./scripts/outputs/transposition-experiment-results/"
        "transposition-experiment-results.jsonl"
    )
    results_path.parent.mkdir(parents=True, exist_ok=True)

    experiment_set = get_config(
        config_path="./scripts/configs/transposition-experiment-config.json",
    )

    pool_type: type[Pool] | type[ThreadPool]
    match experiment_set.target:
        case "local":
            pool_type = Pool
        case _:
            pool_type = ThreadPool

    transposition_tests = [
        TranspositionTestRun(same_states=True)
        for _ in range(experiment_set.same_states_iterations)
    ] + [
        TranspositionTestRun(same_states=False)
        for _ in range(experiment_set.random_states_iterations)
    ]
    random.shuffle(transposition_tests)

    with results_path.open("a") as results_file:
        with pool_type(processes=experiment_set.max_workers) as pool:
            results = pool.imap_unordered(
                run_transposition_test,
                transposition_tests,
            )
            for result in results:
                print(f"{result.key_is_same=}, {result.result_is_same=}")
                results_file.write(result.model_dump_json() + "\n")


def get_config(config_path: str) -> TranspositionExperimentSetConfig:
    with open(config_path, "r") as f:
        return TranspositionExperimentSetConfig.model_validate_json(f.read())


def run_transposition_test(
    params: TranspositionTestRun,
) -> TranspositionTestResult:
    print(f"running...")
    map = get_map()
    state_a = get_state_from_map(map)

    if params.same_states:
        state_b = deepcopy(state_a)
    else:
        state_b = get_state_from_map(map)

    key_a: CacheKey = get_key(state_a)
    key_b: CacheKey = get_key(state_b)
    result_a: AiTreeResult = get_ai_tree_result(state_a)
    result_b: AiTreeResult = get_ai_tree_result(state_b)

    key_is_same = key_a == key_b
    result_is_same = result_a == result_b

    return TranspositionTestResult(
        same_states=params.same_states,
        key_is_same=key_is_same,
        result_is_same=result_is_same,
    )


def get_map() -> GameState:
    """
    Generates an empty state containing just the terrains and boundary.
    """
    # TODO: need PCG for this step. Using a hand-drawn scene for now.
    gs = GameState()
    gs.add_entity(
        MapBoundary(
            vertices=[
                Vec2(0, 0),
                Vec2(200, 0),
                Vec2(200, 200),
                Vec2(0, 200),
            ]
        )
    )
    gs.add_entity(
        TerrainFeature(
            vertices=[
                Vec2(75, 75),
                Vec2(125, 75),
                Vec2(125, 125),
                Vec2(75, 125),
            ],
            flag=TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE,
        )
    )
    return gs


def get_state_from_map(
    map: GameState,
) -> GameState:
    gs = deepcopy(map)
    """
    Given the empty map state, populate with combat units and other entities.
    This makes it a complete state that is game-tree runnable. 
    """

    # TODO: have it randomize initial faction
    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
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
    gs.add_entity(
        RallyStallLoseCondition(
            rally_stall_count=0,
            rally_stall_limit=2,
            last_rallied_faction=None,
        ),
    )

    # Generates 2 blue and 2 red units at random positions.
    # TODO: remove the hardcoding, and make it generates more cases.
    for faction in [
        InitiativeState.Faction.BLUE,
        InitiativeState.Faction.BLUE,
        InitiativeState.Faction.RED,
        InitiativeState.Faction.RED,
    ]:
        gs.add_entity(
            MoveControls(),
            CombatUnit(
                faction=faction,
                status=CombatUnit.Status.ACTIVE,
            ),
            Transform(
                position=Vec2(
                    random.randint(10, 190),
                    random.randint(10, 190),
                ),
                degrees=0,
            ),
            FireControls(fov_degrees=None),
            AssaultControls(),
        )

    return gs


def get_key(
    gs: GameState,
) -> CacheKey:
    return AiTranspositionKeyService.get_key(
        gs=gs,
        transposition_schemes=[
            TranspositionScheme.RoundedPosition(
                type="RoundedPosition",
                to_nearest=1,
            ),
        ],
    )


def get_ai_tree_result(
    gs: GameState,
) -> AiTreeResult:
    """Runs the game-tree and returns its results."""

    gs = deepcopy(gs)
    config = SearchPolicyConfig(
        policy=PolicyConfig.MinimaxPolicy(
            type="MinimaxPolicy",
            depth=4,
        ),
        state=UnabstractedStateConfig(
            type="UnabstractedStateConfig",
            move_candidates_pool=PointsConfig.Grid(
                type="GridConfig",
                spacing=50,
                offset=25,
            ),
            move_candidates_filter=[],
            transposition_schemes=[
                TranspositionScheme.RoundedPosition(
                    type="RoundedPosition",
                    to_nearest=1,
                ),
            ],
        ),
    )
    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.BLUE,
            config=config,
        ),
    )
    # TODO: This AI shenanigans is so messy. Clean this up?
    # The framework isn't built for this kind of use case whatsover.
    state = AiSearchAgent.get_state(gs, config)
    assert isinstance(config.policy, PolicyConfig.MinimaxPolicy)
    action, log = MinimaxPolicy[Action].get_action(
        state=state,
        depth=config.policy.depth,
        log_with_tree=False,
    )
    return AiTreeResult(
        best_action=action,
        value=log.action_value,
    )


if __name__ == "__main__":
    main()
