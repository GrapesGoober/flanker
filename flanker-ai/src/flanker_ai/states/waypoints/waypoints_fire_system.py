from typing import override
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.fire_system import FireSystem


class WaypointsFireSystem(FireSystem):
    @staticmethod
    @override
    def apply_fire_outcome(
        gs: GameState,
        target_id: UUID,
        fire_outcome: FireOutcomes,
    ) -> None:
        # This override is for deterministic minimax.
        # This intends to have minimax prefer singular PIN reactive fire
        # as opposed to double PIN reactive fire.
        # This is achieved by assuming a double PIN makes SUPPRESSED unit.

        target_unit = gs.get_component(target_id, CombatUnit)
        command_system = gs.get(CommandSystem)
        match fire_outcome:
            case FireOutcomes.MISS:
                pass
            case FireOutcomes.PIN:
                if target_unit.status == CombatUnit.Status.ACTIVE:
                    target_unit.status = CombatUnit.Status.PINNED
                elif target_unit.status == CombatUnit.Status.PINNED:
                    target_unit.status = CombatUnit.Status.SUPPRESSED
            case FireOutcomes.SUPPRESS:
                if target_unit.status != CombatUnit.Status.SUPPRESSED:
                    target_unit.status = CombatUnit.Status.SUPPRESSED
                else:  # Kills the unit if it is already suppressed
                    command_system.kill_unit(gs, target_id)
            case FireOutcomes.KILL:
                command_system.kill_unit(gs, target_id)
