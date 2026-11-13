from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib
import pandas as pd
from plotnine import (
    aes,
    facet_wrap,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    theme_matplotlib,
)
from transposition_experiment_models import TranspositionTestResult


@dataclass
class AccuracyTally:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0

    @property
    def total_tests(self) -> int:
        return (
            self.true_positives
            + self.false_positives
            + self.false_negatives
            + self.true_negatives
        )


def main() -> None:
    results_root_path = Path("./scripts/outputs/transposition-experiment-results/")
    result_files = sorted(results_root_path.glob("*.jsonl"))
    if not result_files:
        raise FileNotFoundError(
            f"No transposition result files found in {results_root_path}"
        )

    tally_records: list[dict[str, str]] = []
    for result_file in result_files:
        tally = get_accuracy_tally(get_experiment_results(result_file))
        experiment_name = result_file.stem
        tally_records += [
            {
                "experiment": experiment_name,
                "key_prediction": "Keys same",
                "tree_result": "Values same",
                "count": f"TP: {tally.true_positives}",
            },
            {
                "experiment": experiment_name,
                "key_prediction": "Keys same",
                "tree_result": "Values differ",
                "count": f"FP: {tally.false_positives}",
            },
            {
                "experiment": experiment_name,
                "key_prediction": "Keys differ",
                "tree_result": "Values same",
                "count": f"FN: {tally.false_negatives}",
            },
            {
                "experiment": experiment_name,
                "key_prediction": "Keys differ",
                "tree_result": "Values differ",
                "count": f"TN: {tally.true_negatives}",
            },
            {
                "experiment": experiment_name,
                "key_prediction": "Tree outcome total",
                "tree_result": "Values same",
                "count": (f"Total: " f"{tally.true_positives + tally.false_negatives}"),
            },
            {
                "experiment": experiment_name,
                "key_prediction": "Tree outcome total",
                "tree_result": "Values differ",
                "count": (f"Total: " f"{tally.false_positives + tally.true_negatives}"),
            },
        ]

    df = pd.DataFrame(tally_records)
    matplotlib.use("tkagg")
    plot = (
        ggplot(
            df,
            aes(x="tree_result", y="key_prediction"),
        )
        + geom_tile(fill="white", color="black")
        + geom_text(aes(label="count"))
        + facet_wrap("~experiment")
        + labs(
            x="Tree results",
            y="Transposition keys",
        )
        + theme_matplotlib()
    )
    plot.show()
    plot.save("scripts/outputs/visualize-transposition-accuracy.png")


def get_experiment_results(
    result_file: Path,
) -> Iterable[TranspositionTestResult]:
    with result_file.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield TranspositionTestResult.model_validate_json(line)


def get_accuracy_tally(
    results: Iterable[TranspositionTestResult],
) -> AccuracyTally:
    """
    Counts the true/false positives/negatives of the test results
    of the same experiment.
    """

    tally = AccuracyTally()
    for result in results:
        tree_results_match = result.action_a_value == result.action_b_value
        if result.key_is_same:
            if tree_results_match:
                tally.true_positives += 1
            else:
                tally.false_positives += 1
        elif tree_results_match:
            tally.false_negatives += 1
        else:
            tally.true_negatives += 1
    return tally


if __name__ == "__main__":
    main()
