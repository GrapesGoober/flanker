import random
from copy import deepcopy
from dataclasses import dataclass

from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult, FireAction, MoveAction
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.initiative_system import InitiativeSystem


class AiRandomHeuristicAgent:

    @dataclass
    class ActionResult:
        action: Action
        result: ActionResult

    @staticmethod
    def perform_action(
        gs: GameState,
    ) -> ActionResult | None:
        initiative = InitiativeSystem.get_initiative(gs)

        units = list(gs.query(CombatUnit))
        friendly_ids = [id for id, unit in units if unit.faction == initiative]
        enemy_ids = [id for id, unit in units if unit.faction != initiative]

        fire_actions = [
            FireAction(unit_id=friendly_id, target_id=enemy_id)
            for friendly_id in friendly_ids
            for enemy_id in enemy_ids
        ]

        # If any fire actions are available, perform it
        random.shuffle(fire_actions)
        for fire_action in fire_actions:
            result = ActionSystem.perform(gs, fire_action)
            if not isinstance(result, InvalidAction):
                return deepcopy(
                    AiRandomHeuristicAgent.ActionResult(
                        action=fire_action,
                        result=result,
                    )
                )

        # No fire actions are available, have any random unit move towards
        # any random enemy with any random (not too close) distance.
        move_actions: list[MoveAction] = []
        for friendly_id in friendly_ids:
            friendly_position = gs.get_component(friendly_id, Transform).position
            for enemy_id in enemy_ids:
                enemy_position = gs.get_component(enemy_id, Transform).position
                direction = enemy_position - friendly_position
                if direction.length() == 0:
                    continue

                approach_fraction = random.uniform(0.25, 0.75)
                move_actions.append(
                    MoveAction(
                        unit_id=friendly_id,
                        to=friendly_position + direction * approach_fraction,
                    )
                )

        random.shuffle(move_actions)
        for move_action in move_actions:
            result = ActionSystem.perform(gs, move_action)
            if not isinstance(result, InvalidAction):
                return deepcopy(
                    AiRandomHeuristicAgent.ActionResult(
                        action=move_action,
                        result=result,
                    )
                )

        # To actions available for RH agent
        return None
