import random
from copy import deepcopy
from dataclasses import is_dataclass
from datetime import datetime
from inspect import isclass
from itertools import product
from multiprocessing import Lock
from multiprocessing.pool import Pool, ThreadPool
from multiprocessing.synchronize import Lock as LockType
from pathlib import Path
from time import sleep
from typing import Any, Literal

import requests
from flanker_ai.ai_system import AiSystem
from flanker_ai.config_models import AiConfigComponent, SearchPolicyConfig
from flanker_ai.search_states.common.ai_transposition_key_service import (
    AiTranspositionKeyService,
    CacheKey,
)
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer
from flanker_core.systems.action_system import ActionSystem
from procedural_state_generator import (
    get_game_state,
    get_perturbed_state,
    get_state_from_map,
)
from transposition_experiment_models import (
    ApiTranspositionTestRequest,
    ApiTranspositionTestResponse,
    ApiTreePayoffRequest,
    ApiTreePayoffResponse,
    InputStatePair,
    InputStatePairConfig,
    InputStatePairRecord,
    StatePopulatingMethod,
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
    results_root_path = Path("./scripts/outputs/transposition-experiment-results/")

    # Configs parallel-safe logs
    log_file_path = results_root_path / "run_transposition_experiment.log"
    log_lock: LockType = Lock()
    configure_logging(str(log_file_path), log_lock)

    # Safety check if there are other data still there. Should be a clean run.
    raise_if_results_exists(results_root_path)

    # Get all the input sequences once, to reuse across experiments.
    with get_pool(
        experiment_set=experiment_set,
        log_file_path=log_file_path,
        log_lock=log_lock,
    ) as pool:
        input_sequences_by_name = get_input_sequences(
            experiment_set=experiment_set,
            pool=pool,
        )
    save_sequences_to_file(
        input_sequences_by_name=input_sequences_by_name,
        results_root_path=results_root_path,
    )

    # Init each experiment permutations
    experiments = get_transposition_experiments(
        experiment_set=experiment_set,
        input_sequences_by_name=input_sequences_by_name,
    )
    init_experiment_metadata_files(
        experiments=experiments,
        results_root_path=results_root_path,
    )

    # Generate tests for all experiments.
    transposition_tests = get_all_transposition_tests(
        experiment_configs=experiments,
    )
    random.shuffle(transposition_tests)

    # Run all the tests.
    with get_pool(
        experiment_set=experiment_set, log_file_path=log_file_path, log_lock=log_lock
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


def save_sequences_to_file(
    input_sequences_by_name: dict[str, list[InputStatePair]],
    results_root_path: Path,
) -> None:

    for sequence_name, sequence in input_sequences_by_name.items():
        file_path = results_root_path / f"inputs-{sequence_name}.jsonl"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.is_file():
            return
        with file_path.open("w") as sequence_file:
            sequence_file.writelines(
                InputStatePairRecord(
                    state_a=deserialize_state(input_states.state_a),
                    state_b=deserialize_state(input_states.state_b),
                    tree_a_payoff=input_states.tree_a_payoff,
                    tree_b_payoff=input_states.tree_b_payoff,
                ).model_dump_json(indent=0)
                + "\n"  # Mildly infuriating missing newline
                for input_states in sequence
            )


def get_input_sequences(
    experiment_set: TranspositionExperimentSetConfig,
    pool: Pool | ThreadPool,
) -> dict[str, list[InputStatePair]]:
    map_states: dict[str, GameState] = {
        map_name: get_game_state(
            scene_names=[map_name],
        )
        for map_name in experiment_set.maps
    }
    input_configs: list[InputStatePairConfig] = [
        InputStatePairConfig(
            name=f"{state_method_name}-{map_name}",
            map_state=map_states[map_name],
            state_method=state_method,
            ai_config=experiment_set.game_tree_method,
            target=experiment_set.target,
        )
        for (state_method_name, state_method), map_name in product(
            experiment_set.state_populating_methods.items(),
            experiment_set.maps,
        )
        for _ in range(experiment_set.target_n_tests)
    ]
    input_sequences_by_name: dict[str, list[InputStatePair]] = {}
    results = pool.imap_unordered(
        get_input_state_pair,
        input_configs,
    )
    for name, input_pair in results:
        input_sequences_by_name.setdefault(name, [])
        input_sequences_by_name[name].append(input_pair)
    return input_sequences_by_name


def get_input_state_pair(
    config: InputStatePairConfig,
) -> tuple[str, InputStatePair]:
    log_message(f"Generating state for {config.name}")
    add_ai_configs(config.map_state, config.ai_config)
    state_a = get_state_from_map(config.map_state, initiative="random")

    match config.state_method:
        case StatePopulatingMethod.Random():
            initiative = ActionSystem.get_initiative(state_a)
            state_b = get_state_from_map(config.map_state, initiative=initiative)
        case StatePopulatingMethod.Perturbation():
            state_b = get_perturbed_state(state_a, size=config.state_method.size)

    tree_a_value: float = get_tree_payoff_value(state_a, config.target)
    tree_b_value: float = get_tree_payoff_value(state_b, config.target)

    log_message(f"  Input pair {config.name} done...")

    return config.name, InputStatePair(
        state_a=state_a,
        state_b=state_b,
        tree_a_payoff=tree_a_value,
        tree_b_payoff=tree_b_value,
    )


def get_transposition_experiments(
    experiment_set: TranspositionExperimentSetConfig,
    input_sequences_by_name: dict[str, list[InputStatePair]],
) -> list[TranspositionExperiment]:
    """
    Returns all permutations of experiments given the experiment set config.
    """

    return [  # Oh jeez, this is so disgusting. I should clean this up.
        TranspositionExperiment(
            state_sequence=input_sequences_by_name[f"{state_method_name}-{map_name}"],
            key_methods=key_methods,
            target=experiment_set.target,
            metadata=TranspositionExperimentMetadata(
                name=f"{key_methods_name}-{state_method_name}-{map_name}",
                state_populating_method_name=state_method_name,
                state_populating_method=state_method,
                key_method_name=key_methods_name,
                key_methods=key_methods,
                map_name=map_name,
                n_tests=0,
                target_n_tests=experiment_set.target_n_tests,
            ),
        )
        for (
            (state_method_name, state_method),
            (key_methods_name, key_methods),
            map_name,
        ) in product(
            experiment_set.state_populating_methods.items(),
            experiment_set.transposition_key_methods.items(),
            experiment_set.maps,
        )
    ]


def raise_if_results_exists(
    results_root_path: Path,
) -> None:
    result_files = [
        file
        for pattern in ("*.jsonl", "*.json")
        for file in results_root_path.glob(pattern)
    ]
    if result_files:
        raise FileExistsError(f"Results folder not empty: {', '.join(
                (file.stem for file in result_files),
            )}")
    results_root_path.mkdir(parents=True, exist_ok=True)


def init_experiment_metadata_files(
    experiments: list[TranspositionExperiment],
    results_root_path: Path,
) -> None:
    for experiment in experiments:
        file_path = results_root_path / f"{experiment.metadata.name}-metadata.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.is_file():
            return
        with file_path.open("w") as metadata_file:
            metadata_file.write(experiment.metadata.model_dump_json(indent=2))


def get_all_transposition_tests(
    experiment_configs: list[TranspositionExperiment],
) -> list[TranspositionTestRun]:
    return [
        TranspositionTestRun(
            experiment_name=experiment_config.metadata.name,
            state_a=input_state_pair.state_a,
            state_b=input_state_pair.state_b,
            tree_a_payoff=input_state_pair.tree_a_payoff,
            tree_b_payoff=input_state_pair.tree_b_payoff,
            key_methods=experiment_config.key_methods,
            target=experiment_config.target,
        )
        for experiment_config in experiment_configs
        for input_state_pair in experiment_config.state_sequence
    ]


def run_transposition_test(
    test_run_config: TranspositionTestRun,
) -> tuple[str, TranspositionTestResult]:
    log_message(f"Running transposition test {test_run_config.experiment_name}")

    match test_run_config.target:
        case "local":
            key_a: CacheKey = AiTranspositionKeyService.get_key(
                gs=test_run_config.state_a,
                transposition_schemes=test_run_config.key_methods,
            )
            key_b: CacheKey = AiTranspositionKeyService.get_key(
                gs=test_run_config.state_b,
                transposition_schemes=test_run_config.key_methods,
            )
            key_is_same = key_a == key_b
            test_result = TranspositionTestResult(
                key_is_same=key_is_same,
                tree_a_payoff=test_run_config.tree_a_payoff,
                tree_b_payoff=test_run_config.tree_b_payoff,
            )
        case target_url:
            test_request = ApiTranspositionTestRequest(
                state_a=deserialize_state(test_run_config.state_a),
                state_b=deserialize_state(test_run_config.state_b),
                key_methods=test_run_config.key_methods,
            )
            response: requests.Response | None = None
            while True:  # Keep retrying requests if it fails
                try:
                    response = requests.post(
                        f"{target_url}/api/rpc/experiment/get-transposition-test",
                        json=test_request.model_dump(),
                    )
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    log_message(f"Request had error {e}")
                    log_message(
                        f"Rerunning {test_run_config.experiment_name} in 30 seconds"
                    )
                    sleep(30)
            api_result = ApiTranspositionTestResponse.model_validate_json(response.text)
            test_result = TranspositionTestResult(
                key_is_same=api_result.key_is_same,
                tree_a_payoff=test_run_config.tree_a_payoff,
                tree_b_payoff=test_run_config.tree_b_payoff,
            )

    log_message(f"    {test_run_config.experiment_name} done, recording...")
    return test_run_config.experiment_name, test_result


def get_tree_payoff_value(
    gs: GameState,
    target: Literal["local"] | str,
) -> float:

    match target:
        case "local":
            gs = deepcopy(gs)
            initiative = ActionSystem.get_initiative(gs)
            result = AiSystem.perform_action(gs, initiative)
            if result is None:
                raise RuntimeError("AI can't perform action!")
            if result.policy_log is None:
                raise RuntimeError("Expects a search policy log from AI.")
            return result.policy_log.action_value
        case _:
            request_model = ApiTreePayoffRequest(
                state=deserialize_state(gs),
            )
            response: requests.Response | None = None
            while True:  # Keep retrying requests if it fails
                try:
                    response = requests.post(
                        f"{target}/api/rpc/experiment/get-tree-payoff",
                        json=request_model.model_dump(),
                    )
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    log_message(f"Request had error {e}")
                    log_message(f"Rerunning get-tree-payoff in 30 seconds")
                    sleep(30)
            api_result = ApiTreePayoffResponse.model_validate_json(response.text)
            return api_result.payoff_value


def deserialize_state(
    gs: GameState,
) -> str:
    component_types = [
        component_type
        for _, component_type in vars(components).items()
        if isclass(component_type) and is_dataclass(component_type)
    ]
    component_types.append(AiConfigComponent)
    return Serializer.serialize(
        entities=gs.dump(),
        component_types=component_types,
    )


def add_ai_configs(
    gs: GameState,
    ai_config: SearchPolicyConfig,
) -> None:
    gs.add_entity(
        AiConfigComponent(
            faction=components.InitiativeState.Faction.BLUE,
            config=ai_config,
        ),
    )
    gs.add_entity(
        AiConfigComponent(
            faction=components.InitiativeState.Faction.RED,
            config=ai_config,
        ),
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


def get_pool(
    experiment_set: TranspositionExperimentSetConfig,
    log_file_path: Path,
    log_lock: LockType,
) -> Pool | ThreadPool:

    # Supports local running or if parallelize in cloud use threads for IO.
    pool_type: type[Pool] | type[ThreadPool]
    match experiment_set.target:
        case "local":
            pool_type = Pool
        case _:
            pool_type = ThreadPool

    return pool_type(
        processes=experiment_set.max_workers,
        initializer=configure_logging,
        initargs=(str(log_file_path), log_lock),
    )


if __name__ == "__main__":
    main()
