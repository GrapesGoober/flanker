from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from flanker_ai.ai_agent import AiConfigComponent
from flanker_core.models.components import InitiativeState
from matplotlib.axes import Axes
from pydantic import BaseModel


class MatchResult(BaseModel):
    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class ExperimentResult(BaseModel):
    n_matches: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent
    match_results: list[MatchResult]


def main() -> None:
    scene_1_sizes, scene_2_sizes = get_sizes()
    # plot_kde(scene_1_sizes, scene_2_sizes)
    plot_hist(scene_1_sizes, scene_2_sizes)


def get_sizes() -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    size_grid_scene_1: list[int] = get_search_sizes(
        scene_name="scene-1",
        faction=InitiativeState.Faction.BLUE,
        blue_configs=["grid"],
        red_configs=["grid", "analysis", "rh"],
    )
    size_grid_scene_2: list[int] = get_search_sizes(
        scene_name="scene-2",
        faction=InitiativeState.Faction.BLUE,
        blue_configs=["grid"],
        red_configs=["grid", "analysis", "rh"],
    )
    size_analysis_scene_1: list[int] = get_search_sizes(
        scene_name="scene-1",
        faction=InitiativeState.Faction.BLUE,
        blue_configs=["analysis"],
        red_configs=["grid", "analysis", "rh"],
    )
    size_analysis_scene_2: list[int] = get_search_sizes(
        scene_name="scene-2",
        faction=InitiativeState.Faction.BLUE,
        blue_configs=["analysis"],
        red_configs=["grid", "analysis", "rh"],
    )

    print(
        f"grid-scene-1 average {np.average(size_grid_scene_1)}",
        f"grid-scene-2 average {np.average(size_grid_scene_2)}",
        f"analysis-scene-1 average {np.average(size_analysis_scene_1)}",
        f"analysis-scene-2 average {np.average(size_analysis_scene_2)}",
        sep="\n",
    )

    print(
        f"grid-scene-1 min {min(size_grid_scene_1)}",
        f"grid-scene-2 min {min(size_grid_scene_2)}",
        f"analysis-scene-1 min {min(size_analysis_scene_1)}",
        f"analysis-scene-2 min {min(size_analysis_scene_2)}",
        sep="\n",
    )

    print(
        f"grid-scene-1 max {max(size_grid_scene_1)}",
        f"grid-scene-2 max {max(size_grid_scene_2)}",
        f"analysis-scene-1 max {max(size_analysis_scene_1)}",
        f"analysis-scene-2 max {max(size_analysis_scene_2)}",
        sep="\n",
    )

    scene_1_sizes: dict[str, list[int]] = {
        "grid": size_grid_scene_1,
        "analysis": size_analysis_scene_1,
    }
    scene_2_sizes: dict[str, list[int]] = {
        "grid": size_grid_scene_2,
        "analysis": size_analysis_scene_2,
    }

    return scene_1_sizes, scene_2_sizes


def plot_kde(
    scene_1_sizes: dict[str, list[int]],
    scene_2_sizes: dict[str, list[int]],
) -> None:

    sns.set_style("whitegrid")

    # Init the subplots
    axes: list[Axes]
    fig, axes = plt.subplots(  # type: ignore
        nrows=2,
        ncols=1,
        figsize=(4.5, 4),
        sharex=True,
    )
    CLIP_RANGE = (0, 300_000)

    # Plot scene-1
    for name, sizes in scene_1_sizes.items():
        sns.kdeplot(
            np.array(sizes),
            clip=CLIP_RANGE,
            label=name,
            fill=True,
            ax=axes[0],  # Put into top plot
        )
    axes[0].set_title("scene-1")  # type: ignore
    axes[0].legend()  # type: ignore

    # Plot scene-2
    for name, sizes in scene_2_sizes.items():
        sns.kdeplot(
            np.array(sizes),
            clip=CLIP_RANGE,
            label=name,
            fill=True,
            ax=axes[1],  # Put into bottom plot
        )
    axes[1].set_title("scene-2")  # type: ignore
    axes[1].legend()  # type: ignore

    # Save to file
    fig.tight_layout()
    fig.savefig(  # type: ignore
        "results-treesize.png",
        dpi=300,
        bbox_inches="tight",
    )


def plot_hist(
    scene_1_sizes: dict[str, list[int]],
    scene_2_sizes: dict[str, list[int]],
) -> None:

    FIG_SIZE = (4.5, 4)
    CUTOFF = 200_000
    BINS_COUNT = 20
    Y_LIMIT = 0.5
    FILE_NAME = "searchsizes-comparison.png"

    print(f"Bin width is {CUTOFF/BINS_COUNT}")

    # Create a 2x1 subplot layout (2 rows, 1 column)
    axes: list[Axes]
    fig, axes = plt.subplots(2, 1, figsize=FIG_SIZE, sharex=True)  # type: ignore

    # Loop through scenes and zip them with their corresponding subplot axis
    for ax, search_sizes, scene_name in zip(
        axes,
        [scene_1_sizes, scene_2_sizes],
        ["scene-1", "scene-2"],
    ):
        weights_list = [
            np.ones_like(dataset) / len(dataset)
            for dataset in list(search_sizes.values())
        ]
        ax.hist(  # type: ignore
            x=list(search_sizes.values()),
            range=(0, CUTOFF),
            bins=BINS_COUNT,
            histtype="bar",
            label=["grid", "analysis"],
            weights=weights_list,
        )
        ax.set_ylim(0, Y_LIMIT)
        ax.legend()  # type: ignore
        ax.set_xlabel(f"BLUE game-tree sizes ({scene_name})")  # type: ignore
        ax.set_ylabel("Relative Frequency")  # type: ignore

    fig.tight_layout()
    fig.savefig(  # type: ignore
        FILE_NAME,
        dpi=300,
        bbox_inches="tight",
    )
    # fig.show()  # type: ignore


def get_results(
    experiment_name: str,
) -> ExperimentResult:
    file_path = f"./scripts/experiment_results/{experiment_name}.json"
    with open(file_path, "r") as f:
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file fmpty?!")
        return ExperimentResult.model_validate_json(file_data)


def get_search_sizes(
    scene_name: str,
    faction: InitiativeState.Faction,
    blue_configs: list[str],
    red_configs: list[str],
) -> list[int]:
    # Just a placeholder to return the average
    search_sizes: list[int] = []
    for blue_conf, red_conf in product(blue_configs, red_configs):
        experiment_name = f"{scene_name}-blue-{blue_conf}-red-{red_conf}-experiment"
        results = get_results(experiment_name)
        for match_result in results.match_results:
            match faction:
                case InitiativeState.Faction.BLUE:
                    search_sizes += match_result.blue_search_sizes
                case InitiativeState.Faction.RED:
                    search_sizes += match_result.red_search_sizes
    return search_sizes


if __name__ == "__main__":
    main()
