import random
from copy import deepcopy
from datetime import datetime
from itertools import product
from multiprocessing import Lock
from multiprocessing.pool import Pool, ThreadPool
from multiprocessing.synchronize import Lock as LockType
from pathlib import Path
from typing import Any, Literal

from flanker_ai.ai_system import AiSystem
from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    PolicyConfig,
    SearchPolicyConfig,
    TranspositionScheme,
    UnabstractedStateConfig,
)
from flanker_ai.search_states.common.ai_transposition_key_service import (
    AiTranspositionKeyService,
    CacheKey,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    InitiativeState,
)
from flanker_core.systems.action_system import ActionSystem
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

    # Supports local running or if parallelize in cloud use threads for IO.
    pool_type: type[Pool] | type[ThreadPool]
    match experiment_set.target:
        case "local":
            pool_type = Pool
        case _:
            pool_type = ThreadPool

    results_root_path = Path("./scripts/outputs/transposition-experiment-results/")

    # Configs parallel-safe logs
    log_file_path = results_root_path / "run_transposition_experiment.log"
    log_lock: LockType = Lock()
    configure_logging(str(log_file_path), log_lock)

    # Safety check if there are other data still there.
    # Should be a clean run.
    result_files = [
        file
        for pattern in ("*.jsonl", "*.json")
        for file in results_root_path.glob(pattern)
    ]
    if result_files:
        raise FileExistsError(
            f"Results folder not empty: {', '.join(file.stem for file in result_files)}"
        )
    results_root_path.mkdir(parents=True, exist_ok=True)

    # Get init each experiment permutations
    transposition_experiments = get_transposition_experiments(
        config=experiment_set,
    )
    for experiment in transposition_experiments:
        init_metadata_file(
            experiment_config=experiment,
            results_root_path=results_root_path,
            target_n_tests=experiment_set.target_n_tests,
        )

    # Ensure that the experiments with same state methods
    # use the same states sequence. Ensures consistency between experiments.
    state_sequence_per_method = {
        method: get_state_sequence(method, experiment_set.target_n_tests)
        for method in experiment_set.state_populating_methods
    }

    # Generate tests for all experiments.
    transposition_tests = get_all_transposition_tests(
        transposition_experiments, state_sequence_per_method
    )
    random.shuffle(transposition_tests)

    # Run all the tests.
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
            name=f"{state_method}-{key_methods_name}",
            state_populating_method=state_method,
            key_methods=key_methods,
        )
        for (state_method, (key_methods_name, key_methods)) in product(
            config.state_populating_methods,
            config.zobrist_key_methods.items(),
        )
    ]


def get_all_transposition_tests(
    experiment_configs: list[TranspositionExperiment],
    state_sequence_per_method: dict[str, list[tuple[GameState, GameState]]],
) -> list[TranspositionTestRun]:
    return [
        TranspositionTestRun(
            experiment_name=experiment_config.name,
            state_a=state_a,
            state_b=state_b,
            key_method=experiment_config.key_methods,
        )
        for experiment_config in experiment_configs
        for state_a, state_b in state_sequence_per_method[
            experiment_config.state_populating_method
        ]
    ]


def get_state_sequence(
    method: Literal["random", "perturbation"],
    target_n_tests: int,
) -> list[tuple[GameState, GameState]]:
    state_sequences: list[tuple[GameState, GameState]] = []
    for _ in range(target_n_tests):
        map = get_map()
        state_a = get_state_from_map(map)

        match method:
            case "random":
                state_b = get_state_from_map(map)
            case "perturbation":
                state_b = get_perturbed_state(state_a)

        state_sequences.append((state_a, state_b))
    return state_sequences


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
    action_a_value: float = get_tree_action_value(
        test_run_config.state_a,
    )
    action_b_value: float = get_tree_action_value(
        test_run_config.state_b,
    )

    key_is_same = key_a == key_b

    log_message(f"    {test_run_config.experiment_name} done , recording...")
    return test_run_config.experiment_name, TranspositionTestResult(
        key_is_same=key_is_same,
        action_a_value=action_a_value,
        action_b_value=action_b_value,
    )


def get_key(
    gs: GameState,
    key_methods: list[TranspositionScheme.ALL],
) -> CacheKey:
    return AiTranspositionKeyService.get_key(
        gs=gs,
        transposition_schemes=key_methods,
    )


def get_tree_action_value(
    gs: GameState,
    # target: Literal["local"] | str,
) -> float:
    """Runs the game-tree and returns its action value."""

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
    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.RED,
            config=config,
        ),
    )

    initiative = ActionSystem.get_initiative(gs)
    result = AiSystem.perform_action(gs, initiative)
    if result is None:
        raise RuntimeError("AI can't perform action!")
    if result.policy_log is None:
        raise RuntimeError("Expects a search policy log from AI.")

    return result.policy_log.action_value


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
    results_root_path: Path,
    target_n_tests: int,
) -> None:
    file_path = results_root_path / f"{experiment_config.name}-metadata.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.is_file():
        return

    metadata = TranspositionExperimentMetadata(
        state_populating_method=experiment_config.state_populating_method,
        key_methods=experiment_config.key_methods,
        n_tests=0,
        target_n_tests=target_n_tests,
    )
    with file_path.open("w") as metadata_file:
        metadata_file.write(metadata.model_dump_json(indent=2))


def get_metadata(
    experiment_name: str,
    results_root_path: Path,
) -> TranspositionExperimentMetadata:
    file_path = results_root_path / f"{experiment_name}-metadata.json"
    if not file_path.is_file():
        raise FileNotFoundError(f"Metadata file for {experiment_name} does not exist")

    file_data = file_path.read_text()
    if not file_data:
        raise ValueError(f"{file_path} file is empty")
    return TranspositionExperimentMetadata.model_validate_json(file_data)


def record_transposition_test_result(
    experiment_name: str,
    result: TranspositionTestResult,
    results_root_path: Path,
) -> None:
    metadata = get_metadata(experiment_name, results_root_path)
    if metadata.n_tests >= metadata.target_n_tests:
        return
    metadata.n_tests += 1

    metadata_path = results_root_path / f"{experiment_name}-metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Metadata file for {experiment_name} does not exist")
    metadata_path.write_text(metadata.model_dump_json(indent=2))

    result_path = results_root_path / f"{experiment_name}.jsonl"
    with result_path.open("a") as results_file:
        results_file.write(result.model_dump_json())
        results_file.write("\n")


if __name__ == "__main__":
    main()
