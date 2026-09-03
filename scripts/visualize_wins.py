import json
from itertools import product
from pathlib import Path
from typing import TypedDict

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


class _WinRateCell(TypedDict):
    scene: str
    blue: str
    red: str
    win_rate: float


def main() -> None:

    # Retrieve the each experiment results
    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiment_results_by_name = {
        name: get_experiment_result(
            experiment_name=name,
            results_root_path="./scripts/outputs/experiment-results/",
        )
        for name in get_experiment_names(experiment_set)
    }

    # Can only plot from one match settings
    match_setting = experiment_set.match_settings[0]

    # Generate a list of win rate for each cells
    cells: list[_WinRateCell] = [
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

    # Plot those cells
    df = pd.DataFrame(cells)
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
    experiment_results_by_name: dict[str, ExperimentResult],
) -> float:
    experiment = experiment_results_by_name[experiment_name]

    return (
        sum(
            result.winner == InitiativeState.Faction.BLUE
            for result in experiment.match_results
        )
        / experiment.n_matches
    )


if __name__ == "__main__":
    main()
