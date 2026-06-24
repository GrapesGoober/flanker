from itertools import product

import matplotlib.pyplot as plt
from flanker_ai.ai_agent import AiConfigComponent
from flanker_core.models.components import InitiativeState
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

    SCENE_NAME = "scene-2"
    BLUE_CONFIGS_TO_SHOW: list[str] = ["grid", "analysis"]
    FIG_SIZE = (4.5, 2)

    all_search_sizes: list[list[int]] = []
    for blue_config in BLUE_CONFIGS_TO_SHOW:
        search_sizes = get_search_sizes(
            scene_name=SCENE_NAME,
            faction=InitiativeState.Faction.BLUE,
            blue_configs=[blue_config],
            red_configs=["grid", "analysis", "rh"],
        )
        all_search_sizes.append(search_sizes)

    fig, ax = plt.subplots(figsize=FIG_SIZE)  # type: ignore

    ax.hist(  # type: ignore
        x=all_search_sizes,
        range=(0, 200_000),
        bins=30,
        histtype="bar",
        label=BLUE_CONFIGS_TO_SHOW,
    )
    ax.legend()  # type: ignore
    ax.set_xlabel("Search size")  # type: ignore
    ax.set_ylabel("Count")  # type: ignore

    fig.tight_layout()
    fig.savefig(  # type: ignore
        f"searchsizes-{SCENE_NAME}.png",
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
