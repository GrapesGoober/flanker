from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, FireControls
from flanker_core.systems.objective_system import ObjectiveSystem


class CommandSystem:
    """ECS System class for command hierarchy mechanic."""

    @staticmethod
    def kill_unit(gs: GameState, unit_id: UUID) -> None:
        """Kills a combat unit while transferring chain of command."""

        unit = gs.get_component(unit_id, CombatUnit)

        # Reset fire controls if firing at this unit
        for _, fire_controls in gs.query(FireControls):
            if fire_controls.firing_at == None:
                continue
            firing_id, _ = fire_controls.firing_at
            if firing_id != unit_id:
                continue
            fire_controls.firing_at = None

        # Finds the next chain of command to reassign current command
        current_command = unit.command_id
        next_command: UUID | None = None
        for id, child_unit in gs.query(CombatUnit):
            if child_unit.command_id != unit_id:
                continue
            # Records first subordinate unit as the command
            if next_command == None:
                next_command = id
                child_unit.command_id = current_command
            # Make the rest subordinate to new command, if exists
            else:
                child_unit.command_id = next_command

        ObjectiveSystem.count_kill(gs, unit_id)
        gs.delete_entity(unit_id)
