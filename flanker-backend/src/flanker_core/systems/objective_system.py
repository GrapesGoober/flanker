from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationWinCondition,
    InitiativeState,
    RallyStallLoseCondition,
    StallLoseCondition,
)


class ObjectiveSystem:
    """Static system class for scenario objectives"""

    @staticmethod
    def count_kill(
        gs: GameState,
        unit_destroyed_id: UUID,
    ) -> None:
        """Count a killed unit towards Elimination Objective."""
        unit = gs.get_component(unit_destroyed_id, CombatUnit)
        for _, objective in gs.query(EliminationWinCondition):
            if objective.target_faction != unit.faction:
                continue
            objective.units_eliminated_counter += 1

    @staticmethod
    def get_winning_faction(
        gs: GameState,
    ) -> InitiativeState.Faction | None:
        """Get the winning faction, `None` if no winner yet."""
        for _, objective in gs.query(EliminationWinCondition):
            if objective.units_eliminated_counter >= objective.units_to_eliminate:
                return objective.winning_faction
        for _, counter in gs.query(StallLoseCondition):
            if counter.stall_count > counter.stall_limit:
                return counter.winning_faction
        for _, counter in gs.query(RallyStallLoseCondition):
            if counter.rally_stall_count > counter.rally_stall_limit:
                match counter.last_rallied_faction:
                    case InitiativeState.Faction.BLUE:
                        return InitiativeState.Faction.RED
                    case InitiativeState.Faction.RED:
                        return InitiativeState.Faction.BLUE
                    case None:
                        raise RuntimeError(
                            "Unexpected control path! "
                            "Last rally action isn't tracked!"
                        )

    @staticmethod
    def count_stall(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> None:
        """Count up the number of stalling moves for the given faction."""
        for _, counter in gs.query(StallLoseCondition):
            if counter.counting_faction == faction:
                counter.stall_count += 1

    @staticmethod
    def count_rally_stall(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> None:
        """Count up the number of stalling rallies for the given faction."""
        for _, counter in gs.query(RallyStallLoseCondition):
            counter.rally_stall_count += 1
            counter.last_rallied_faction = faction

    @staticmethod
    def reset_stall(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> None:
        """Resets the number of stalling moves for the given faction."""
        for _, counter in gs.query(StallLoseCondition):
            if counter.counting_faction == faction:
                counter.stall_count = 0

    @staticmethod
    def reset_rally_stall(
        gs: GameState,
    ) -> None:
        """Resets the number of stalling rallies for the given faction."""
        for _, counter in gs.query(RallyStallLoseCondition):
            counter.rally_stall_count = 0
            counter.last_rallied_faction = None
