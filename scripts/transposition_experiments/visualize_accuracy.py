from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Iterable

import pandas as pd
from transposition_experiment_models import (
    TranspositionExperimentMetadata,
    TranspositionExperimentSetConfig,
    TranspositionTestResult,
)


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
    experiment_set = get_config(
        config_path="./scripts/configs/transposition-experiment-config.json",
    )
    results_root_path = Path("./scripts/outputs/transposition-experiment-results/")
    experiment_names = get_experiment_names(experiment_set)
    df = get_formatted_table(
        results_root_path,
        experiment_names,
    )
    latex_table = df.to_latex(index=False)
    for rule in ("\\toprule", "\\midrule", "\\bottomrule"):
        latex_table = latex_table.replace(rule, "\\hline")
    Path("scripts/outputs/confusion-matrix.tex").write_text(
        latex_table,
        encoding="utf-8",
    )


def get_formatted_table(
    results_root_path: Path,
    experiment_names: list[str],
) -> pd.DataFrame:
    tally_records: list[dict[str, str | int]] = []
    for experiment_name in experiment_names:
        metadata_path = results_root_path / f"{experiment_name}-metadata.json"
        results_path = results_root_path / f"{experiment_name}.jsonl"
        metadata = get_experiment_metadata(metadata_path)
        tally = get_accuracy_tally(get_experiment_results(results_path))
        tally_records.append(
            {
                "State": f"{metadata.state_populating_method.type}",
                "Key": "-".join(
                    [key_method.type for key_method in metadata.key_methods]
                ),
                "TP": tally.true_positives,
                "FP": tally.false_positives,
                "TN": tally.true_negatives,
                "FN": tally.false_negatives,
                "P": (tally.true_positives + tally.false_negatives),
                "N": (tally.false_positives + tally.true_negatives),
            }
        )

    return pd.DataFrame(tally_records)


def get_experiment_results(
    result_file: Path,
) -> Iterable[TranspositionTestResult]:
    with result_file.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield TranspositionTestResult.model_validate_json(line)


def get_experiment_metadata(
    metadata_file: Path,
) -> TranspositionExperimentMetadata:
    with metadata_file.open("r", encoding="utf-8") as file:
        return TranspositionExperimentMetadata.model_validate_json(
            file.read(),
        )


def get_config(config_path: str) -> TranspositionExperimentSetConfig:
    with open(config_path, "r") as f:
        return TranspositionExperimentSetConfig.model_validate_json(f.read())


def get_experiment_names(
    experiment_set: TranspositionExperimentSetConfig,
) -> list[str]:
    """
    Returns all permutations of experiments given the experiment set config.
    """

    return [
        f"{state_method_name}-{key_methods_name}-{map_name}"
        for (
            (state_method_name, _),
            (key_methods_name, _),
            map_name,
        ) in product(
            experiment_set.state_populating_methods.items(),
            experiment_set.transposition_key_methods.items(),
            experiment_set.maps,
        )
    ]


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
