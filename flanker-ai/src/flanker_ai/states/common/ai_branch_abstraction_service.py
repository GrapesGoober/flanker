from flanker_ai.actions import Action, FireAction
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, FireControls


class AiBranchAbstractionService:

    @staticmethod
    def _find_one_mergable_branch_pair(
        branches: list[tuple[float, GameState]],
        action: Action,
    ) -> tuple[int, int] | None:
        """
        Returns a pair of branch indices that are considered mergable.
        This uses a simple criteria that the two units must be the same.
        """
        for left_id, (_, branch_left) in enumerate(branches):
            for right_id, (_, branch_right) in enumerate(branches):
                if left_id == right_id:
                    continue
                unit_left = branch_left.try_component(action.unit_id, CombatUnit)
                unit_right = branch_right.try_component(action.unit_id, CombatUnit)
                if unit_left != unit_right:
                    continue

                match action:
                    case FireAction():
                        unit_left_fire = branch_left.try_component(
                            action.unit_id, FireControls
                        )
                        unit_right_fire = branch_left.try_component(
                            action.unit_id, FireControls
                        )
                        if unit_left_fire != unit_right_fire:
                            continue
                    case _:
                        ...

                return (left_id, right_id)
        return None

    @staticmethod
    def merge_branches(
        branches: list[tuple[float, GameState]],
        action: Action,
    ) -> list[tuple[float, GameState]]:
        """Merge similar branches with similar outcomes, if any."""
        if branches == []:
            raise ValueError("The provided branches list is empty.")

        new_branches: list[tuple[float, GameState]] = list(branches)

        # Keep merging until can't merge no more.
        while True:
            # Find a pair that can be merged
            pair = AiBranchAbstractionService._find_one_mergable_branch_pair(
                new_branches, action
            )
            if pair == None:
                break

            # Pair found, add a new merged branch. Assume that the
            # left branch is considered representative of both branches.
            left_index, right_index = pair
            left_probability, left_branch = new_branches[left_index]
            right_probability, _ = new_branches[right_index]
            new_probability = left_probability + right_probability
            new_state = left_branch

            # Update the list of branches
            new_branches[left_index] = (new_probability, new_state)
            new_branches.pop(right_index)
        return new_branches

    @staticmethod
    def get_one_approximate_branch(
        branches: list[tuple[float, GameState]],
        action: Action,
    ) -> GameState:
        """
        Returns one most representative approximate branch.
        The criteria is to pick the most likely branch to happen, after merged.
        """
        merged_branches = AiBranchAbstractionService.merge_branches(branches, action)
        _, branch = max(merged_branches, key=lambda b: b[0])
        return branch
