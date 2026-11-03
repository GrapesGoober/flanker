import random
from copy import deepcopy
from datetime import datetime
from itertools import product
from multiprocessing import Lock
from multiprocessing.pool import Pool, ThreadPool
from multiprocessing.synchronize import Lock as LockType
from pathlib import Path
from typing import Any, Literal

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
    InitiativeState,
)
from procedural_state_generator import (
    get_map,
    get_perturbed_state,
    get_state_from_map,
)
from transposition_experiment_models import (
    TranspositionExperiment,
    TranspositionExperimentMetadata,
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
    results_root_path = "./scripts/outputs/transposition-experiment-results/"
    for experiment in transposition_experiments:
        init_metadata_file(experiment, results_root_path)

    transposition_tests = [
        transposition_test
        for experiment_config in transposition_experiments
        for transposition_test in get_transposition_tests(
            config=experiment_config,
            results_root_path=results_root_path,
        )
    ]
    random.shuffle(transposition_tests)

    results_root = Path(results_root_path)
    results_root.mkdir(parents=True, exist_ok=True)
    log_file_path = results_root / "run_transposition_experiment.log"
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
            record_transposition_test_result(
                experiment_name=experiment_name,
                result=result,
                results_root_path=results_root_path,
            )


def get_config(config_path: str) -> TranspositionExperimentSetConfig:
    with open(config_path, "r") as f:
        return TranspositionExperimentSetConfig.model_validate_json(f.read())


def get_transposition_experiments(
    config: TranspositionExperimentSetConfig,
) -> list[TranspositionExperiment]:
    return [
        TranspositionExperiment(
            name=get_experiment_name(state_method, key_method),
            state_populating_method=state_method,
            key_method=key_method,
            n_tests=config.n_tests,
        )
        for (state_method, key_method) in product(
            config.state_populating_methods,
            config.zobrist_key_methods,
        )
    ]


def get_experiment_name(
    state_method: Literal["random", "perturbation"],
    key_method: TranspositionScheme.ALL,
) -> str:
    state_name = f"{state_method}"
    match key_method:
        case TranspositionScheme.RoundedPosition():
            key_name = f"{key_method.type}-r{key_method.to_nearest}".lower()
        case TranspositionScheme.RoundedRotation():
            key_name = f"{key_method.type}-r{key_method.to_nearest}".lower()
        case TranspositionScheme.LosSignatures():
            key_name = key_method.type.lower()
            if key_method.with_fov:
                key_name += "-fov"
    return f"{state_name}-{key_name}"


def get_transposition_tests(
    config: TranspositionExperiment,
    results_root_path: str,
) -> list[TranspositionTestRun]:
    metadata = get_metadata(config.name, results_root_path)
    remaining_tests = max(0, config.n_tests - metadata.n_tests)
    if remaining_tests == 0:
        return []

    tests: list[TranspositionTestRun] = []
    for _ in range(remaining_tests):

        map = get_map()
        state_a = get_state_from_map(map)

        match config.state_populating_method:
            case "random":
                state_b = get_state_from_map(map)
            case "perturbation":
                state_b = get_perturbed_state(state_a)

        tests.append(
            TranspositionTestRun(
                experiment_name=config.name,
                state_a=state_a,
                state_b=state_b,
                key_method=config.key_method,
            )
        )

    return tests


def run_transposition_test(
    test_run_config: TranspositionTestRun,
) -> tuple[str, TranspositionTestResult]:
    log_message(f"Running transposition test {test_run_config.experiment_name}")

    key_a: CacheKey = get_key(
        test_run_config.state_a,
        test_run_config.key_method,
    )
    key_b: CacheKey = get_key(
        test_run_config.state_b,
        test_run_config.key_method,
    )
    tree_a_value: float = get_ai_tree_value(
        test_run_config.state_a,
    )
    tree_b_value: float = get_ai_tree_value(
        test_run_config.state_b,
    )

    key_is_same = key_a == key_b

    log_message(f"    {test_run_config.experiment_name} done , recording...")
    return test_run_config.experiment_name, TranspositionTestResult(
        key_is_same=key_is_same,
        tree_a_value=tree_a_value,
        tree_b_value=tree_b_value,
    )


def get_key(
    gs: GameState,
    key_method: TranspositionScheme.ALL,
) -> CacheKey:
    return AiTranspositionKeyService.get_key(
        gs=gs,
        transposition_schemes=[key_method],
    )


def get_ai_tree_value(
    gs: GameState,
) -> float:
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
                spacing=100,
                offset=50,
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
    _, log = MinimaxPolicy[Action].get_action(
        state=state,
        depth=config.policy.depth,
        log_with_tree=False,
    )
    return log.action_value


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


def init_metadata_file(
    experiment_config: TranspositionExperiment,
    results_root_path: str,
) -> None:
    file_path = Path(results_root_path) / f"{experiment_config.name}-metadata.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.is_file():
        return

    metadata = TranspositionExperimentMetadata(
        state_populating_method=experiment_config.state_populating_method,
        key_method=experiment_config.key_method,
        n_tests=0,
        target_n_tests=experiment_config.n_tests,
    )
    with file_path.open("w") as metadata_file:
        metadata_file.write(metadata.model_dump_json(indent=2))


def get_metadata(
    experiment_name: str,
    results_root_path: str,
) -> TranspositionExperimentMetadata:
    file_path = Path(results_root_path) / f"{experiment_name}-metadata.json"
    if not file_path.is_file():
        raise FileNotFoundError(f"Metadata file for {experiment_name} does not exist")

    file_data = file_path.read_text()
    if not file_data:
        raise ValueError(f"{file_path} file is empty")
    return TranspositionExperimentMetadata.model_validate_json(file_data)


def record_transposition_test_result(
    experiment_name: str,
    result: TranspositionTestResult,
    results_root_path: str,
) -> None:
    metadata = get_metadata(experiment_name, results_root_path)
    if metadata.n_tests >= metadata.target_n_tests:
        return
    metadata.n_tests += 1

    metadata_path = Path(results_root_path) / f"{experiment_name}-metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Metadata file for {experiment_name} does not exist")
    metadata_path.write_text(metadata.model_dump_json(indent=2))

    result_path = Path(results_root_path) / f"{experiment_name}.jsonl"
    with result_path.open("a") as results_file:
        results_file.write(result.model_dump_json())
        results_file.write("\n")


if __name__ == "__main__":
    main()
