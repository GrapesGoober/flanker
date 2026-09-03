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
        name: get_results(name, results_root_path)
        for name in get_experiment_names(experiment_set)
    }
    match_settings_to_plot = experiment_set.match_settings[0]

    # Plot win rate for each scene
    win_rates_list: list[Any] = []
    for idx, scene_name in enumerate(experiment_set.scene_configs):

        # Create a BLUE's win rate mapping for each BLUE and each RED pairing
        win_rates: dict[str, dict[str, float]] = {
            blue_config: {
                red_config: 0.1  # TODO: put the experiment_results here
                for red_config in experiment_set.red_configs
            }
            for blue_config in experiment_set.blue_configs
        }
        win_rates_list.append(win_rates)

    plot = plot_win_rates(win_rates_list, experiment_set.scene_configs)
    plot.draw(show=True)


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


def get_results(
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


def get_win_rates(
    blue_configs: list[str],
    red_configs: list[str],
    scene_name: str,
    results_root_path: str,
) -> list[list[float]]:
    win_rates: list[list[float]] = []

    for blue in blue_configs:
        cells: list[float] = []
        win_rates.append(cells)
        for red in red_configs:
            match_results = get_results(
                experiment_name=f"{scene_name}-blue-{blue}-red-{red}-experiment",
                results_root_path=results_root_path,
            ).match_results
            blue_wins = sum(
                match_result.winner == InitiativeState.Faction.BLUE
                for match_result in match_results
            )
            cells.append(blue_wins / len(match_results))

    return win_rates


if __name__ == "__main__":
    main()
