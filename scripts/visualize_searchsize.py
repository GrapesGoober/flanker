from itertools import product
from pathlib import Path
from typing import Iterable

import matplotlib
import pandas as pd
from experiment_models import ExperimentSetConfig, MatchResult
from plotnine import (
    aes,
    geom_histogram,
    ggplot,
    theme_matplotlib,
    theme_set,
)


def main() -> None:

    # Retrieve the each experiment results
    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiment_results_by_name: dict[str, list[MatchResult]] = {
        name: list(
            get_experiment_result(
                experiment_name=name,
                results_root_path="./scripts/outputs/experiment-results/",
            )
        )
        for name in get_experiment_names(experiment_set)
    }

    # Can only plot from one match settings
    match_setting = experiment_set.match_settings[0]

    # Generate cells of each win rate to render
    blue_config = "blue-grid"
    df = pd.DataFrame(
        [
            {
                "scene": scene_name,
                "blue": blue_config,
                "red": red_config,
                "search_size": blue_search_size,
            }
            for scene_name in experiment_set.scene_configs
            for red_config in experiment_set.red_configs
            for match_result in experiment_results_by_name[
                "-".join(
                    [scene_name, blue_config, red_config, match_setting],
                )
            ]
            for blue_search_size in match_result.blue_search_sizes
        ]
    )

    matplotlib.use("tkagg")
    theme_set(theme_matplotlib())
    plot = ggplot(df, aes(x="search_size")) + geom_histogram()
    plot.show()


def get_config(config_path: str) -> ExperimentSetConfig:
    with open(config_path, "r") as f:
        return ExperimentSetConfig.model_validate_json(f.read())


def get_experiment_names(
    experiment_set: ExperimentSetConfig,
) -> list[str]:
    return [
        "-".join(name for name in combination)
        for combination in product(
            experiment_set.scene_configs,
            experiment_set.blue_configs,
            experiment_set.red_configs,
            experiment_set.match_settings,
        )
    ]


def get_experiment_result(
    experiment_name: str,
    results_root_path: str,
) -> Iterable[MatchResult]:
    file_path = Path(results_root_path) / f"{experiment_name}.jsonl"
    if not Path(file_path).is_file():
        raise Exception(f"Results file for {experiment_name} does not exist")

    with open(file_path, "r") as f:
        # This file reading is unreliable... need better file IO?
        for line in f:
            yield MatchResult.model_validate_json(line)


if __name__ == "__main__":
    main()
