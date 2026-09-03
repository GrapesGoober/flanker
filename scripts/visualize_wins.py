import json
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd
from experiment_models import ExperimentResult, ExperimentSetConfig
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
    results_root_path = "./scripts/outputs/experiment-results/"

    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiment_results = {
        name: get_experiment_result(name, results_root_path)
        for name in get_experiment_names(experiment_set)
    }

    # Can only plot from one match settings
    match_setting = experiment_set.match_settings[0]

    # Plot win rate for each scene
    win_rates_list: list[Any] = []
    for scene_name in experiment_set.scene_configs:
        # Create a BLUE's win rate mapping for each BLUE and each RED pairing
        win_rates: dict[str, dict[str, float]] = {
            blue_config: {
                red_config: get_win_rate(
                    experiment_name="-".join(
                        [scene_name, blue_config, red_config, match_setting],
                    ),
                    experiment_results=experiment_results,
                )
                for red_config in experiment_set.red_configs
            }
            for blue_config in experiment_set.blue_configs
        }
        win_rates_list.append(win_rates)

    plot = plot_win_rates(win_rates_list, experiment_set.scene_configs)
    plot.draw(show=True)


def get_config(config_path: str) -> ExperimentSetConfig:
    with open(config_path, "r") as f:
        return ExperimentSetConfig(**json.loads(f.read()))


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
) -> ExperimentResult:
    file_path = f"{results_root_path}{experiment_name}.json"
    if not Path(file_path).is_file():
        raise Exception(f"Results file for {experiment_name} does not exist")

    with open(file_path, "r") as f:
        # This file reading is unreliable... need better file IO?
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file empty?!")
        return ExperimentResult.model_validate_json(file_data)


def get_win_rate(
    experiment_name: str,
    experiment_results: dict[str, ExperimentResult],
) -> float:
    experiment = experiment_results[experiment_name]

    return (
        sum(
            result.winner == InitiativeState.Faction.BLUE
            for result in experiment.match_results
        )
        / experiment.n_matches
    )


def plot_win_rates(
    win_rates_list: list[dict[str, dict[str, float]]], titles: list[str]
) -> ggplot:
    rows: list[dict[str, Any]] = []

    for win_rates, title in zip(win_rates_list, titles):
        for blue, red_rates in win_rates.items():
            for red, win_rate in red_rates.items():
                rows.append(
                    {
                        "plot": title,
                        "blue": blue,
                        "red": red,
                        "win_rate": win_rate,
                    }
                )

    df = pd.DataFrame(rows)

    return (
        ggplot(df, aes(x="red", y="blue", fill="win_rate"))
        + geom_tile()
        + geom_text(
            aes(label="win_rate"),
        )
        + scale_fill_cmap(
            limits=(0, 1),
        )
        + facet_wrap("~plot", nrow=1)
        + labs(
            x="RED configuration",
            y="BLUE configuration",
        )
    )


if __name__ == "__main__":
    main()
