from copy import deepcopy
from flanker_ai.i_game_state_converter import IGameStateConverter
from flanker_ai.i_ai_policy import IAiPolicy
from flanker_ai.unabstracted.models import ActionResult
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem

_MAX_ACTION_PER_INITIATIVE = 20

class AiAgent:
    def __init__[TAction](
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        converter: IGameStateConverter[TAction],
        policy: IAiPolicy[TAction],
    ) -> None:
        self._raw_gs = gs
        self._faction: InitiativeState.Faction = faction
        self._converter = converter
        self.policy = policy
        self._template_gs = converter.create_template(gs)
        
    def play_initiative(self) -> list[ActionResult]:
        """Have the agent play the entire initiative."""

        if InitiativeSystem.get_initiative(self._raw_gs) != self._faction:
            return []

        halt_counter = 0
        action_results: list[ActionResult] = []
        while InitiativeSystem.get_initiative(self._raw_gs) == self._faction:
            if ObjectiveSystem.get_winning_faction(self._raw_gs) != None:
                break
            # Prepare the template into state usable for AI
            gs = self._converter.update_template(
                self._raw_gs,
                self._template_gs,
            )
            # Check redundant moves (stop search)
            if halt_counter > _MAX_ACTION_PER_INITIATIVE:
                print(f"{self._faction.value} AI made useless actions, breaking")
                InitiativeSystem.flip_initiative(self._raw_gs)
                break
            # Runs the abstracted graph search
            action = self.policy.get_action_sequence(gs)
            print(f"{self._faction.value} AI made action: {action}")

            if action == []:
                print(f"No valid action for {self._faction.value} AI, breaking")
                InitiativeSystem.flip_initiative(self._raw_gs)
                break

            result = self._converter.apply_action(
                action[0], # TODO: make have the initiative take action sequence
                representation=gs
            )
            if isinstance(result, InvalidAction):
                print(f"{self._faction.value} AI made invalid action, breaking")
                InitiativeSystem.flip_initiative(self._raw_gs)
                break
            # These result objects would be used for logging
            # Thus, prevent mutation by creating a copy
            action_results.append(deepcopy(result))
            halt_counter += 1

        return action_results
