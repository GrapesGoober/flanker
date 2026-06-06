from typing import Sequence

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class AiActionService:

    @staticmethod
    def get_actions(
        gs: GameState,
        initiative: InitiativeState.Faction,
        move_candidates: list[Vec2],
    ) -> Sequence[Action]:
        los_system = gs.get(LosSystem)

        # Generate an action for each combat unit
        actions: list[Action] = []
        for friendly_id, unit in gs.query(CombatUnit):
            if unit.faction != initiative:
                continue

            # Adds assault & fire actions for each friendly-enemy pair
            for target_id, target in gs.query(CombatUnit):
                if target.faction == initiative:
                    continue
                actions.append(
                    FireAction(
                        unit_id=friendly_id,
                        target_id=target_id,
                    )
                )
                actions.append(
                    AssaultAction(
                        unit_id=friendly_id,
                        target_id=target_id,
                    )
                )

            # Add move and pivot actions.
            # Have it pivot only towards enemies to reduce branching factor.
            friendly_transform = gs.get_component(friendly_id, Transform)
            for target_id, target in gs.query(CombatUnit):
                if target.faction == initiative:
                    continue

                # Only pivot if not already looking there.
                enemy_transform = gs.get_component(target_id, Transform)
                if los_system.in_fov(
                    spotter_transform=friendly_transform,
                    target_pos=enemy_transform.position,
                ):
                    continue
                if not los_system.has_los(
                    gs,
                    spotter_pos=friendly_transform.position,
                    target_pos=enemy_transform.position,
                ):
                    continue

                actions.append(
                    PivotAction(
                        unit_id=friendly_id,
                        to=enemy_transform.position,
                    )
                )

            # Adds move actions last, for best alpha-beta pruning.
            for move_position in move_candidates:
                actions.append(
                    MoveAction(
                        unit_id=friendly_id,
                        to=move_position,
                    )
                )

        return actions
