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


def get_results(experiment_name: str) -> ExperimentResult:
    file_path = f"./scripts/experiment_results/{experiment_name}.json"
    with open(file_path, "r") as f:
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file fmpty?!")
        return ExperimentResult.model_validate_json(file_data)


def get_win_rates(
    result_names: list[list[str]],
) -> list[list[float]]:

    win_rates: list[list[float]] = []
    for row in result_names:
        current_row: list[float] = []
        win_rates.append(current_row)
        for result_name in row:
            match_results = get_results(result_name).match_results
            blue_wins = sum(
                match_result.winner == InitiativeState.Faction.BLUE
                for match_result in match_results
            )
            total_matches = len(match_results)
            current_row.append(round(blue_wins / total_matches, ndigits=1))

    return win_rates


def main() -> None:

    result_names = [
        [
            "scene-2-blue-grid-red-rh-experiment",
            "scene-2-blue-analysis-red-rh-experiment",
            "scene-2-blue-rh-red-rh-experiment",
        ],
    ]

    win_rates = get_win_rates(result_names)

    plt.imshow(win_rates)  # type: ignore
    plt.colorbar(label="Win Rate")  # type: ignore
    plt.show()  # type: ignore


if __name__ == "__main__":
    main()
