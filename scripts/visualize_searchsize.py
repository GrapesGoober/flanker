from itertools import product

import matplotlib.pyplot as plt
from flanker_ai.ai_agent import AiConfigComponent
from flanker_core.models.components import InitiativeState
from matplotlib.axes import Axes
from numpy import average
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

    SCENES = ["scene-1", "scene-2"]  # Modified to support two scenes
    BLUE_CONFIGS_TO_SHOW: list[str] = ["grid", "analysis"]
    FIG_SIZE = (4.5, 4)
    CUTOFF = 200_000
    BINS_COUNT = 20

    print(f"Bin width is {CUTOFF/BINS_COUNT}")

    # Create a 2x1 subplot layout (2 rows, 1 column)
    axes: list[Axes]
    fig, axes = plt.subplots(2, 1, figsize=FIG_SIZE, sharex=True)  # type: ignore

    # Loop through scenes and zip them with their corresponding subplot axis
    search_sizes_across_scenes: dict[str, list[int]] = {}
    for ax, scene_name in zip(axes, SCENES):
        all_search_sizes: list[list[int]] = []
        for blue_config in BLUE_CONFIGS_TO_SHOW:
            search_sizes = get_search_sizes(
                scene_name=scene_name,
                faction=InitiativeState.Faction.BLUE,
                blue_configs=[blue_config],
                red_configs=["grid", "analysis", "rh"],
            )
            search_sizes_across_scenes.setdefault(blue_config, [])
            search_sizes_across_scenes[blue_config] += search_sizes
            all_search_sizes.append(search_sizes)

        ax.hist(  # type: ignore
            x=all_search_sizes,
            range=(0, CUTOFF),
            bins=BINS_COUNT,
            histtype="bar",
            label=BLUE_CONFIGS_TO_SHOW,
            density=True,
        )
        ax.legend()  # type: ignore
        ax.set_xlabel(f"BLUE game-tree sizes ({scene_name})")  # type: ignore
        ax.set_ylabel("Probability Density")  # type: ignore

    for conf, search_sizes in search_sizes_across_scenes.items():
        print(f"Average of {conf} = {average(search_sizes)}")
        print(f"Length of {conf} = {len(search_sizes)}")

    fig.tight_layout()
    fig.savefig(  # type: ignore
        f"searchsizes-comparison.png",
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
