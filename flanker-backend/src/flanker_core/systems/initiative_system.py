from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, FireControls, InitiativeState
from flanker_core.models.outcomes import FireEffect


class InitiativeSystem:
    """ECS System class for initiative mechanic."""

    # TODO: this flip_initiative is not idempotent. This smells bad.
    # Perhaps the initiative should be handled at the action level?
    # If so, it keeps intiatives mutation centralized and idempotent.
    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Mutates the current initiative to the other faction."""
        for _, initiative in gs.query(InitiativeState):
            match initiative.faction:
                case InitiativeState.Faction.RED:
                    initiative.faction = InitiativeState.Faction.BLUE
                case InitiativeState.Faction.BLUE:
                    initiative.faction = InitiativeState.Faction.RED
        InitiativeSystem._update_unit_status(gs)

    @staticmethod
    def set_initiative(gs: GameState, faction: InitiativeState.Faction) -> None:
        """Mutates the given faction to have the initiative."""
        for _, initiative_state in gs.query(InitiativeState):
            initiative_state.faction = faction
        InitiativeSystem._update_unit_status(gs)

    @staticmethod
    def has_initiative(gs: GameState, unit_id: UUID) -> bool:
        """Check whether the unit's faction has initiative."""
        unit = gs.get_component(unit_id, CombatUnit)
        return unit.faction == InitiativeSystem.get_initiative(gs)

    @staticmethod
    def get_initiative(gs: GameState) -> InitiativeState.Faction:
        """Get the faction that has the current initiative."""
        for _, faction in gs.query(InitiativeState):
            return faction.faction
        raise Exception("InitiativeState component not found")

    @staticmethod
    def _update_unit_status(
        gs: GameState,
    ) -> None:
        """Updates unit status of a combat unit using fire effects."""

        for unit_id, unit in gs.query(CombatUnit):

            if unit.faction != InitiativeSystem.get_initiative(gs):
                continue

            # Record each fire effects of each firer
            fire_effects: set[FireEffect] = set()
            for _, fire_controls in gs.query(FireControls):
                if fire_controls.firing_at == None:
                    continue
                fire_at_id, fire_effect = fire_controls.firing_at
                if fire_at_id != unit_id:
                    continue
                fire_effects.add(fire_effect)

            # Apply each fire effect; SUPPRESSING surpass PINNING
            if FireEffect.SUPPRESSING in fire_effects:
                unit.status = CombatUnit.Status.SUPPRESSED
            elif fire_effects == {FireEffect.PINNING}:
                unit.status = CombatUnit.Status.PINNED
            else:
                unit.status = CombatUnit.Status.ACTIVE
