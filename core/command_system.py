from core.gamestate import GameState
from core.components import CombatUnit
from core.objective_system import ObjectiveSystem


class CommandSystem:
    """ECS System class for command hierarchy mechanic."""

    @staticmethod
    def kill_unit(gs: GameState, unit_id: int) -> None:
        """Kills a combat unit while transferring down chain of command."""

        unit = gs.get_component(unit_id, CombatUnit)
        current_command = unit.command_id

        # Finds the next chain of command
        next_command: int | None = None
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
