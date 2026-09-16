from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, FireControls
from flanker_core.systems.objective_system import ObjectiveSystem


class CommandSystem:
    """ECS System class for command hierarchy mechanic."""

    @staticmethod
    def kill_unit(gs: GameState, unit_id: UUID) -> None:
        """Kills a combat unit."""

        unit = gs.try_component(unit_id, CombatUnit)
        if unit == None:
            raise ValueError(f"The {unit_id=} is not a Combat Unit.")

        # Reset fire controls if firing at this unit
        for _, fire_controls in gs.query(FireControls):
            if fire_controls.firing_at == None:
                continue
            firing_id, _ = fire_controls.firing_at
            if firing_id != unit_id:
                continue
            fire_controls.firing_at = None

        ObjectiveSystem.count_kill(gs, unit_id)
        gs.delete_entity(unit_id)
