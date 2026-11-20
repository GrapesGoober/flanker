from dataclasses import dataclass
from itertools import product
from math import isclose
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

    key_method_name: str
    map_name: str
    state_populating_method_name: str
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int

    def to_row(self) -> dict[str, str | int]:
        return {
            "Key Method": self.key_method_name,
            "Input States": f"{self.state_populating_method_name}-{self.map_name}",
            "TP": self.true_positives,
            "TN": self.true_negatives,
            "FP": self.false_positives,
            "FN": self.false_negatives,
            "P": self.true_positives + self.false_negatives,
            "N": self.true_negatives + self.false_positives,
        }


def main() -> None:
    experiment_set = get_config(
        config_path="./scripts/configs/transposition-experiment-config.json",
    )
    results_root_path = Path("./scripts/outputs/transposition-experiment-results/")
    experiment_names = get_experiment_names(experiment_set)
    tallies = get_formatted_table(
        results_root_path,
        experiment_names,
    )
    totals = get_totals_per_method(tallies)
    df = pd.DataFrame([record.to_row() for record in tallies + totals])
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
) -> list[AccuracyTally]:
    tally_records: list[AccuracyTally] = []
    for experiment_name in experiment_names:
        metadata_path = results_root_path / f"{experiment_name}-metadata.json"
        results_path = results_root_path / f"{experiment_name}.jsonl"
        tally = get_accuracy_tally(
            results=get_experiment_results(results_path),
            metadata=get_experiment_metadata(metadata_path),
        )
        tally_records.append(tally)
    tally_records.sort(
        key=lambda record: (
            record.key_method_name,
            record.state_populating_method_name,
            record.map_name,
        )
    )
    return tally_records


def get_totals_per_method(
    tallies: list[AccuracyTally],
) -> list[AccuracyTally]:
    """
    Aggregates the total TP, TN, FP, FN values per each unique key methods.
    """
    totals_by_method: dict[str, AccuracyTally] = {}
    for tally in tallies:
        totals_by_method.setdefault(
            tally.key_method_name,
            AccuracyTally(
                key_method_name=tally.key_method_name,
                map_name="Total",
                state_populating_method_name="Total",
                true_positives=0,
                false_positives=0,
                false_negatives=0,
                true_negatives=0,
            ),
        )
        total = totals_by_method[tally.key_method_name]
        total.true_positives += tally.true_positives
        total.false_positives += tally.false_positives
        total.false_negatives += tally.false_negatives
        total.true_negatives += tally.true_negatives
    return list(totals_by_method.values())


def get_experiment_results(
    result_path: Path,
) -> Iterable[TranspositionTestResult]:
    with result_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield TranspositionTestResult.model_validate_json(line)


def get_experiment_metadata(
    metadata_path: Path,
) -> TranspositionExperimentMetadata:
    with metadata_path.open("r", encoding="utf-8") as file:
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
        f"{key_methods_name}-{state_method_name}-{map_name}"
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
    metadata: TranspositionExperimentMetadata,
) -> AccuracyTally:
    """
    Counts the true/false positives/negatives of the test results
    of the same experiment.
    """

    tally = AccuracyTally(
        key_method_name=metadata.key_method_name,
        map_name=metadata.map_name,
        state_populating_method_name=metadata.state_populating_method_name,
        true_positives=0,
        false_positives=0,
        false_negatives=0,
        true_negatives=0,
    )
    for result in results:
        tree_results_match = isclose(
            result.tree_a_payoff,
            result.tree_b_payoff,
            rel_tol=1e-2,
        )

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
