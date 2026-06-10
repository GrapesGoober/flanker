from typing import Sequence
from uuid import UUID

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
        divide_moves_per_unit: bool,
    ) -> Sequence[Action]:
        los_system = gs.get(LosSystem)

        # Build a list of combat units
        friendly_ids: list[UUID] = []
        target_ids: list[UUID] = []
        for unit_id, unit in gs.query(CombatUnit):
            if unit.faction == initiative:
                friendly_ids.append(unit_id)
            elif unit.faction != initiative:
                target_ids.append(unit_id)

        # Build a list of actions for each action type
        actions: list[Action] = []
        actions += AiActionService.get_attack_actions(
            friendly_units=friendly_ids, target_units=target_ids
        )

        for friendly_id, unit in gs.query(CombatUnit):
            if unit.faction != initiative:
                continue

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

    @staticmethod
    def get_attack_actions(
        friendly_units: list[UUID],
        target_units: list[UUID],
    ) -> list[Action]:
        actions: list[Action] = []
        for friendly_id in friendly_units:
            # Adds assault & fire actions for each friendly-enemy pair
            for target_id in target_units:
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

        return actions
