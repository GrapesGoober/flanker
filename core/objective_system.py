from core.components import CombatUnit, EliminationObjective, Faction
from core.gamestate import GameState


class ObjectiveSystem:
    """Static system class for scenario objectives"""

    @staticmethod
    def count_kill(gs: GameState, unit_destroyed_id: int) -> None:
        unit = gs.get_component(unit_destroyed_id, CombatUnit)
        for _, objective in gs.query(EliminationObjective):
            if objective.target_faction != unit.faction:
                continue
            objective.units_destroyed_counter += 1

    @staticmethod
    def get_winning_faction(gs: GameState) -> int | None:
        for id, _, objective in gs.query(Faction, EliminationObjective):
            if objective.units_destroyed_counter == objective.units_to_destroy:
                return id
