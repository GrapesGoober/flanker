import random
from copy import deepcopy
from datetime import datetime
from multiprocessing import Lock
from multiprocessing.pool import Pool, ThreadPool
from multiprocessing.synchronize import Lock as LockType
from pathlib import Path
from typing import Any

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
from transposition_experiment_models import (
    AiTreeResult,
    TranspositionExperiment,
    TranspositionExperimentSetConfig,
    TranspositionTestResult,
    TranspositionTestRun,
)

_log_file_path: str | None = None
_log_lock: LockType | None = None


def main() -> None:

    experiment_set = get_config(
        config_path="./scripts/configs/transposition-experiment-config.json",
    )

    pool_type: type[Pool] | type[ThreadPool]
    match experiment_set.target:
        case "local":
            pool_type = Pool
        case _:
            pool_type = ThreadPool

    transposition_experiments = get_transposition_experiments(
        config=experiment_set,
    )
    transposition_tests = [
        transposition_test
        for experiment_config in transposition_experiments
        for transposition_test in get_transposition_tests(
            config=experiment_config,
        )
    ]
    random.shuffle(transposition_tests)

    results_root_path = Path("./scripts/outputs/transposition-experiment-results/")
    results_root_path.mkdir(parents=True, exist_ok=True)
    log_file_path = results_root_path / "run_transposition_experiment.log"
    log_lock: LockType = Lock()
    configure_logging(str(log_file_path), log_lock)

    with pool_type(
        processes=experiment_set.max_workers,
        initializer=configure_logging,
        initargs=(str(log_file_path), log_lock),
    ) as pool:
        results = pool.imap_unordered(
            run_transposition_test,
            transposition_tests,
        )
        for experiment_name, result in results:
            log_message(f"    {experiment_name} done, tallying")
            results_path = results_root_path / f"{experiment_name}.jsonl"
            with results_path.open("a", encoding="utf-8") as results_file:
                results_file.write(result.model_dump_json())
                results_file.write("\n")


def get_config(config_path: str) -> TranspositionExperimentSetConfig:
    with open(config_path, "r") as f:
        return TranspositionExperimentSetConfig.model_validate_json(f.read())


def get_transposition_experiments(
    config: TranspositionExperimentSetConfig,
) -> list[TranspositionExperiment]:
    # TODO: add experiments permutations here, if needed.
    # For now, I only have one possible permutation, thus one experiment.
    return [
        TranspositionExperiment(
            name="randomly-populated",
            state_populating_method=config.state_populating_method,
            n_tests=config.n_tests,
        )
    ]


def get_transposition_tests(
    config: TranspositionExperiment,
) -> list[TranspositionTestRun]:
    map = get_map()
    state_a = get_state_from_map(map)

    match config.state_populating_method:
        case "random":
            state_b = get_state_from_map(map)

    return [
        TranspositionTestRun(
            experiment_name=config.name,
            state_a=state_a,
            state_b=state_b,
        )
        for _ in range(config.n_tests)
    ]


def run_transposition_test(
    test_run_config: TranspositionTestRun,
) -> tuple[str, TranspositionTestResult]:
    log_message(f"Running transposition test {test_run_config.experiment_name}")

    key_a: CacheKey = get_key(test_run_config.state_a)
    key_b: CacheKey = get_key(test_run_config.state_b)
    result_a: AiTreeResult = get_ai_tree_result(test_run_config.state_a)
    result_b: AiTreeResult = get_ai_tree_result(test_run_config.state_b)

    key_is_same = key_a == key_b
    result_is_same = result_a == result_b

    log_message(f"    finished {test_run_config.experiment_name}, recording...")
    return test_run_config.experiment_name, TranspositionTestResult(
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


def configure_logging(log_file_path: str, log_lock: Any) -> None:
    global _log_file_path, _log_lock
    _log_file_path = log_file_path
    _log_lock = log_lock


def log_message(message: str) -> None:
    print(message)
    if _log_file_path is None or _log_lock is None:
        raise RuntimeError("Experiment file logging has not been configured")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with _log_lock:
        with open(_log_file_path, "a") as log_file:
            log_file.write(f"{timestamp}\t{message}\n")


if __name__ == "__main__":
    main()
