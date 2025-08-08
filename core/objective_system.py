from core.components import EliminationObjective, Faction
from core.faction_system import FactionSystem
from core.gamestate import GameState


class ObjectiveSystem:
    """Static system class for scenario objectives"""

    @staticmethod
    def count_kill(gs: GameState, unit_destroyed_id: int) -> None:
        for _, objective in gs.query(EliminationObjective):
            if objective.target_faction_id != FactionSystem.get_faction_id(
                gs, unit_destroyed_id
            ):
                continue
            objective.units_destroyed_counter += 1

    @staticmethod
    def get_winning_faction(gs: GameState) -> int | None:
        for id, _, objective in gs.query(Faction, EliminationObjective):
            if objective.units_destroyed_counter == objective.units_to_destroy:
                return id
