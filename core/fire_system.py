import random
from core.command_system import CommandSystem
from core.components import CombatUnit, FireControls, Transform
from core.events import FireActionInput, MoveStepEvent
from core.gamestate import GameState
from core.faction_system import InitiativeSystem
from core.los_system import LosSystem
from test_event import EventRegistry


class FireSystem:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def _validate_fire_action(
        gs: GameState,
        target_id: int,
        attacker_id: int,
        is_reactive: bool,
    ) -> bool:

        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)

        # Check if attacker can attack
        if attacker_unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return False
        if is_reactive and InitiativeSystem.has_initiative(gs, attacker_id):
            return False  # No initiative for reactive fire
        if not is_reactive and not InitiativeSystem.has_initiative(gs, attacker_id):
            return False

        # Check that the target faction is not the same as attacker
        if attacker_unit.faction == target_unit.faction:
            return False

        # Check if target is in line of sight
        if not LosSystem.check(gs, attacker_id, target_id):
            return False

        return True

    @staticmethod
    def _fire(
        gs: GameState,
        target_id: int,
        attacker_id: int,
    ) -> FireControls.Outcomes:

        target_unit = gs.get_component(target_id, CombatUnit)
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        fire_controls = gs.get_component(attacker_id, FireControls)

        # Determine fire outcome, using overriden value if found
        override = fire_controls.override
        if override:
            outcome = float(override)
        else:
            outcome = random.random()

        # Apply outcome
        # TODO: for fire reaction, should support multiple shooter
        if outcome <= FireControls.Outcomes.MISS:
            InitiativeSystem.set_initiative(gs, target_unit.faction)
            return FireControls.Outcomes.MISS
        elif outcome <= FireControls.Outcomes.PIN:
            if target_unit.status != CombatUnit.Status.SUPPRESSED:
                target_unit.status = CombatUnit.Status.PINNED
            InitiativeSystem.set_initiative(gs, target_unit.faction)
            return FireControls.Outcomes.PIN
        elif outcome <= FireControls.Outcomes.SUPPRESS:
            target_unit.status = CombatUnit.Status.SUPPRESSED
            InitiativeSystem.set_initiative(gs, attacker_unit.faction)
            return FireControls.Outcomes.SUPPRESS
        elif outcome <= FireControls.Outcomes.KILL:
            CommandSystem.kill_unit(gs, target_id)
            InitiativeSystem.set_initiative(gs, attacker_unit.faction)
            return FireControls.Outcomes.KILL

        raise Exception(f"Invalid fire outcome {outcome=}")

    @EventRegistry.on(FireActionInput)
    @staticmethod
    def fire(gs: GameState, input: FireActionInput) -> None:
        """
        Performs fire action from attacker unit to target unit.
        Returns `True` if success.
        """
        if not FireSystem._validate_fire_action(
            gs=gs,
            target_id=input.target_id,
            attacker_id=input.attacker_id,
            is_reactive=False,
        ):
            return
        FireSystem._fire(
            gs=gs,
            target_id=input.target_id,
            attacker_id=input.attacker_id,
        )

    @EventRegistry.on(MoveStepEvent)
    @staticmethod
    def reactive_fire(gs: GameState, event: MoveStepEvent) -> None:
        unit = gs.get_component(event.unit_id, CombatUnit)
        valid_spotter_id: int | None = None
        valid_fire_controls: FireControls | None = None
        for spotter_id, spotter_unit, _, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):

            # Check that spotter is a valid spotter for reactive fire
            if spotter_id == event.unit_id:
                continue
            if unit.faction == spotter_unit.faction:
                continue
            if fire_controls.can_reactive_fire == False:
                continue
            if not LosSystem.check(gs, spotter_id, event.unit_id):
                continue

            if not FireSystem._validate_fire_action(
                gs=gs,
                target_id=event.unit_id,
                attacker_id=spotter_id,
                is_reactive=True,
            ):
                continue

            valid_spotter_id = spotter_id
            valid_fire_controls = fire_controls

        if valid_spotter_id != None and valid_fire_controls != None:
            result = FireSystem._fire(
                gs=gs,
                target_id=event.unit_id,
                attacker_id=valid_spotter_id,
            )

            if result >= FireControls.Outcomes.PIN:
                event.is_interrupted = True

            if result == FireControls.Outcomes.MISS:
                valid_fire_controls.can_reactive_fire = False
