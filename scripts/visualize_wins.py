import json
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
from experiment_models import ExperimentResult, ExperimentSetConfig
from flanker_core.models.components import InitiativeState
from matplotlib.axes import Axes

# pyright: reportUnknownMemberType=false


def main() -> None:
    results_root_path = "./scripts/outputs/experiment-results/"

    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiment_results = {
        name: get_results(name, results_root_path)
        for name in get_experiment_names(experiment_set)
    }
    ...


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


def old_main() -> None:
    blue_configs = ["grid", "analysis", "rh", "mcts"]
    red_configs = ["rh"]
    scenes = ["scene-1", "scene-2"]
    FONTSIZE = 20

    # Create a figure with 1 row and 2 columns
    axes: list[Axes]
    _, axes = plt.subplots(1, 2, figsize=(8, 4))  # type: ignore

    for idx, scene_name in enumerate(scenes):
        ax = axes[idx]
        win_rates = get_win_rates(
            blue_configs=blue_configs,
            red_configs=red_configs,
            scene_name=scene_name,
            results_root_path="./scripts/outputs/experiment-results/",
        )

        ax.imshow(win_rates, vmin=0, vmax=1)  # type: ignore

        ax.set_xticks(range(len(red_configs)))  # type: ignore
        ax.set_xticklabels(red_configs, fontsize=FONTSIZE)  # type: ignore
        ax.set_xlabel("Red", fontsize=FONTSIZE)  # type: ignore
        ax.set_title(scene_name, fontsize=FONTSIZE)  # type: ignore

        if idx == 0:
            ax.set_ylabel("Blue", fontsize=FONTSIZE)  # type: ignore
            ax.set_yticks(range(len(blue_configs)))  # type: ignore
            ax.set_yticklabels(blue_configs, fontsize=FONTSIZE)  # type: ignore
        else:
            ax.set_yticks([])  # type: ignore

        # Add numbers to each cell
        for i in range(len(win_rates)):
            for j in range(len(win_rates[i])):
                ax.text(  # type: ignore
                    j,
                    i,
                    f"{win_rates[i][j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=FONTSIZE,
                    color="white" if win_rates[i][j] < 0.5 else "black",
                )

    plt.tight_layout()
    # plt.savefig("scenes_winrates_comparison.png", bbox_inches="tight")  # type: ignore
    plt.show()


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
