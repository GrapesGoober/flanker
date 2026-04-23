from typing import override

from flanker_ai.components import AiStallCountComponent, InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.systems.objective_system import ObjectiveSystem

_MAX_STALL_LIMIT = 5


class AiObjectiveSystem(ObjectiveSystem):
    @staticmethod
    @override
    def get_winning_faction(gs: GameState) -> InitiativeState.Faction | None:

        if entities := gs.query(AiStallCountComponent):
            _, stall_component = entities[0]
        else:
            gs.add_entity(stall_component := AiStallCountComponent())

        for faction, counter in stall_component.stall_counter.items():
            if counter > _MAX_STALL_LIMIT:
                # mark faction as losing
                if faction == InitiativeState.Faction.BLUE:
                    return InitiativeState.Faction.RED
                elif faction == InitiativeState.Faction.RED:
                    return InitiativeState.Faction.BLUE

        return ObjectiveSystem.get_winning_faction(gs)
