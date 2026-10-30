from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.actions import RallyActionResult
from flanker_core.models.components import CombatUnit
from flanker_core.models.outcomes import RallyOutcomes
from flanker_core.systems.objective_system import ObjectiveSystem


class CommandSystem:
    """ECS System class for command hierarchy mechanic."""

    @staticmethod
    def kill_unit(
        gs: GameState,
        unit_id: UUID,
    ) -> None:
        """Kills a combat unit."""

        unit = gs.try_component(unit_id, CombatUnit)
        if unit == None:
            raise ValueError(f"The {unit_id=} is not a Combat Unit.")

        ObjectiveSystem.count_kill(gs, unit_id)
        gs.delete_entity(unit_id)

    @staticmethod
    def rally(
        gs: GameState,
        unit_id: UUID,
    ) -> RallyActionResult:
        """
        Rallies a unit. If success, the unit status recovers to active.
        Loses initiative otherwise.
        """

        unit = gs.get_component(unit_id, CombatUnit)

        # TODO: This is a deterministic rally for now.
        # Will make this probabilistic later.
        if unit.status == CombatUnit.Status.ACTIVE:
            ObjectiveSystem.count_rally_stall(
                gs=gs,
                faction=unit.faction,
            )
            return RallyActionResult(
                outcome=RallyOutcomes.FAIL,
            )
        else:
            ObjectiveSystem.reset_rally_stall(gs)

            unit.status = CombatUnit.Status.ACTIVE

            return RallyActionResult(
                outcome=RallyOutcomes.SUCCESS,
            )
