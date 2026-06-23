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

    configs = ["grid", "analysis", "rh"]
    win_rates = get_win_rates(
        blue_configs=configs,
        red_configs=configs,
        scene_name="scene-1",
    )

    fig, ax = plt.subplots()  # type: ignore
    FONTSIZE = 20
    im = ax.imshow(win_rates, vmin=0, vmax=1)  # type: ignore

    ax.set_xticks(range(len(configs)))  # type: ignore
    ax.set_xticklabels(configs, fontsize=FONTSIZE)  # type: ignore
    ax.set_yticks(range(len(configs)))  # type: ignore
    ax.set_yticklabels(configs, fontsize=FONTSIZE)  # type: ignore
    ax.set_xlabel("Blue", fontsize=FONTSIZE)  # type: ignore
    ax.set_ylabel("Red", fontsize=FONTSIZE)  # type: ignore

    cbar = fig.colorbar(im, ax=ax, label="Win Rate")  # type: ignore
    cbar.ax.tick_params(labelsize=FONTSIZE)  # type: ignore
    cbar.set_label("Win Rate", fontsize=16)  # type: ignore

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
    plt.savefig("scene-1.png", bbox_inches="tight")  # type: ignore


def get_results(experiment_name: str) -> ExperimentResult:
    file_path = f"./scripts/experiment_results/{experiment_name}.json"
    with open(file_path, "r") as f:
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file fmpty?!")
        return ExperimentResult.model_validate_json(file_data)


def get_win_rates(
    blue_configs: list[str],
    red_configs: list[str],
    scene_name: str,
) -> list[list[float]]:
    win_rates: list[list[float]] = []

    for red in red_configs:
        cells: list[float] = []
        win_rates.append(cells)
        for blue in blue_configs:
            match_results = get_results(
                f"{scene_name}-blue-{blue}-red-{red}-experiment"
            ).match_results
            blue_wins = sum(
                match_result.winner == InitiativeState.Faction.BLUE
                for match_result in match_results
            )
            cells.append(blue_wins / len(match_results))

    return win_rates


if __name__ == "__main__":
    main()
