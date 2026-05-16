from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from flanker_ai.states.unabstracted.ai_branching_service import AiBranchingService
from flanker_core.models.outcomes import FireOutcomes


@dataclass
class Fixture:
    enemy_1: UUID = uuid4()
    enemy_2: UUID = uuid4()


@pytest.fixture
def fixture() -> Fixture:
    return Fixture()


def test_permutation_one_outcome(fixture: Fixture) -> None:
    permutations = AiBranchingService.get_permutations(
        unit_ids={fixture.enemy_1},
        outcome_probabilities={FireOutcomes.SUPPRESS: 1},
    )
    assert permutations == [
        (1, {fixture.enemy_1: FireOutcomes.SUPPRESS}),
    ]


def test_permutation_two_outcomes(fixture: Fixture) -> None:
    permutations = AiBranchingService.get_permutations(
        unit_ids={fixture.enemy_1},
        outcome_probabilities={
            FireOutcomes.PIN: 0.6,
            FireOutcomes.SUPPRESS: 0.4,
        },
    )
    assert permutations == [
        (0.6, {fixture.enemy_1: FireOutcomes.PIN}),
        (0.4, {fixture.enemy_1: FireOutcomes.SUPPRESS}),
    ]


def test_permutation_four_outcomes(fixture: Fixture) -> None:
    permutations = AiBranchingService.get_permutations(
        unit_ids={fixture.enemy_1, fixture.enemy_2},
        outcome_probabilities={
            FireOutcomes.PIN: 0.6,
            FireOutcomes.SUPPRESS: 0.4,
        },
    )
    assert len(permutations) == 4

    # The PIN/SUPPRESS combo is unordered, so I use 'in' operator instead
    assert (
        0.36,
        {
            fixture.enemy_1: FireOutcomes.PIN,
            fixture.enemy_2: FireOutcomes.PIN,
        },
    ) in permutations

    assert (
        0.24,
        {
            fixture.enemy_1: FireOutcomes.PIN,
            fixture.enemy_2: FireOutcomes.SUPPRESS,
        },
    ) in permutations

    assert (
        0.24,
        {
            fixture.enemy_1: FireOutcomes.SUPPRESS,
            fixture.enemy_2: FireOutcomes.PIN,
        },
    ) in permutations

    assert (
        # Floating point imprecision means that this isn't exactly 0.16
        0.4 * 0.4,
        {
            fixture.enemy_1: FireOutcomes.SUPPRESS,
            fixture.enemy_2: FireOutcomes.SUPPRESS,
        },
    ) in permutations
