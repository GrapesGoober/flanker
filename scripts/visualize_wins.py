from itertools import product
from pathlib import Path
from typing import Iterable

import pandas as pd
from experiment_models import ExperimentSetConfig, MatchResult
from flanker_core.models.components import InitiativeState
from plotnine import (
    aes,
    facet_wrap,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_cmap,
)


def main() -> None:

    # Retrieve the each experiment results
    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiment_results_by_name: dict[str, list[MatchResult]] = {
        name: list(
            get_experiment_results(
                experiment_name=name,
                results_root_path="./scripts/outputs/experiment-results/",
            )
        )
        for name in get_experiment_names(experiment_set)
    }

    # Can only plot from one match settings
    match_setting = experiment_set.match_settings[0]

    # Generate cells of each win rate to render
    df = pd.DataFrame(
        [
            {
                "scene": scene_name,
                "blue": blue_config,
                "red": red_config,
                "win_rate": get_win_rate(
                    experiment_name="-".join(
                        [scene_name, blue_config, red_config, match_setting],
                    ),
                    experiment_results_by_name=experiment_results_by_name,
                ),
            }
            for scene_name in experiment_set.scene_configs
            for blue_config in experiment_set.blue_configs
            for red_config in experiment_set.red_configs
        ]
    )

    # Plot those cells
    plot = (
        ggplot(df, aes(x="red", y="blue", fill="win_rate"))
        + geom_tile()
        + geom_text(aes(label="win_rate"))
        + scale_fill_cmap(limits=(0, 1))
        + facet_wrap("~scene", nrow=1)
        + labs(
            x="RED configuration",
            y="BLUE configuration",
        )
    )
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


def get_experiment_results(
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


def get_win_rate(
    experiment_name: str,
    experiment_results_by_name: dict[str, list[MatchResult]],
) -> float:
    match_results = experiment_results_by_name[experiment_name]
    return sum(
        match_result.winner == InitiativeState.Faction.BLUE
        for match_result in match_results
    ) / len(match_results)


if __name__ == "__main__":
    main()
