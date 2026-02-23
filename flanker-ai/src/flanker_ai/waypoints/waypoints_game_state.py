import random
from dataclasses import dataclass

from flanker_ai.i_game_state import IGameState
from flanker_ai.waypoints.models import (
    WaypointAction,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
)
from flanker_ai.waypoints.waypoints_scheme import replace
from flanker_core.models.components import (
    CombatUnit,
    EliminationObjective,
    InitiativeState,
)
from flanker_core.models.vec2 import Vec2


@dataclass
class AbstractedCombatUnit:
    # Note: this should be kept flat to be serializable
    unit_id: int
    current_waypoint_id: int
    status: CombatUnit.Status
    faction: InitiativeState.Faction
    no_fire: bool


@dataclass
class WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


class WaypointsGameState(IGameState[WaypointAction]):
    def __init__(
        self,
        waypoints: dict[int, WaypointNode],
        combat_units: dict[int, AbstractedCombatUnit],
        initiative: InitiativeState.Faction,
        objectives: list[EliminationObjective],
    ) -> None:
        self.waypoints = waypoints
        self.combat_units = combat_units
        self.initiative = initiative
        self.objectives = objectives

    def copy(self) -> "WaypointsGameState":
        copied_units = {id: replace(unit) for id, unit in self.combat_units.items()}
        copied_objectives = [replace(obj) for obj in self.objectives]
        return WaypointsGameState(
            waypoints=self.waypoints,
            combat_units=copied_units,
            initiative=self.initiative,
            objectives=copied_objectives,
        )

    def get_score(self) -> float:
        winner = self.get_winner()
        if winner == InitiativeState.Faction.BLUE:
            return 10000
        elif winner == InitiativeState.Faction.RED:
            return -10000

        score = 0.0
        for unit in self.combat_units.values():
            value = 0
            match unit.status:
                case CombatUnit.Status.ACTIVE:
                    value = 3
                case CombatUnit.Status.PINNED:
                    value = 2
                case CombatUnit.Status.SUPPRESSED:
                    value = 1

            if unit.faction == InitiativeState.Faction.BLUE:
                score += value
            else:
                score -= value
        return score

    def get_actions(self) -> list[WaypointAction]:

        actions: list[WaypointAction] = []
        friendly_units: list[tuple[int, AbstractedCombatUnit]] = []
        enemy_units: list[tuple[int, AbstractedCombatUnit]] = []
        for combat_unit_id, combat_unit in self.combat_units.items():
            if combat_unit.faction == self.initiative:
                friendly_units.append((combat_unit_id, combat_unit))
            if combat_unit.faction != self.initiative:
                enemy_units.append((combat_unit_id, combat_unit))

        for combat_unit_id, combat_unit in friendly_units:
            current_waypoint = self.waypoints[combat_unit.current_waypoint_id]
            if combat_unit.faction != self.initiative:
                continue

            # Adds assault & fire actions
            for enemy_id, enemy_unit in enemy_units:

                # Add fire action if the enemy is on a visible node
                if enemy_unit.faction == combat_unit.faction:
                    continue
                if combat_unit.status in [
                    CombatUnit.Status.ACTIVE,
                    CombatUnit.Status.PINNED,
                ]:
                    if enemy_unit.current_waypoint_id in current_waypoint.visible_nodes:
                        actions.append(
                            WaypointFireAction(
                                unit_id=combat_unit_id,
                                target_id=enemy_id,
                            )
                        )

                # Add an assault action
                if combat_unit.status == CombatUnit.Status.ACTIVE:
                    # Only assault there if it's movable
                    if (
                        enemy_unit.current_waypoint_id
                        not in current_waypoint.movable_paths.keys()
                    ):
                        continue
                    interrupt = self._get_move_interrupt(
                        combat_unit, enemy_unit.current_waypoint_id
                    )
                    actions.append(
                        WaypointAssaultAction(
                            unit_id=combat_unit_id,
                            target_id=enemy_id,
                            interrupt_at_id=interrupt,
                        )
                    )

            # Adds move actions later, for best alpha-beta pruning
            # TODO: is this causing the speed decrease for 3v3?
            # It creates new population list every branch
            if combat_unit.status == CombatUnit.Status.ACTIVE:
                # Filter some move actions to reduce branching factor
                movable_nodes = random.sample(
                    population=list(current_waypoint.movable_paths.keys()),
                    k=10,
                )

                for move_to_id in movable_nodes:
                    interrupt = self._get_move_interrupt(
                        combat_unit,
                        move_to_id,
                    )
                    actions.append(
                        WaypointMoveAction(
                            unit_id=combat_unit_id,
                            move_to_waypoint_id=move_to_id,
                            interrupt_at_id=interrupt,
                        )
                    )

        return actions

    def get_branches(
        self,
        action: WaypointAction,
    ) -> list["WaypointsGameState"]:

        match action:
            case WaypointMoveAction():
                gs = self.copy()
                current_unit = gs.combat_units[action.unit_id]
                # Check for move interrupts
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now
                    current_unit.status = CombatUnit.Status.PINNED
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = action.move_to_waypoint_id
                return [gs]

            case WaypointFireAction():
                gs = self.copy()
                # Assumes determinic for now
                target_unit = gs.combat_units[action.target_id]
                target_unit.status = CombatUnit.Status.SUPPRESSED
                return [gs]

            case WaypointAssaultAction():
                gs = self.copy()
                # Check for move interrupts
                current_unit = gs.combat_units[action.unit_id]
                target_unit = gs.combat_units[action.target_id]
                if action.interrupt_at_id is not None:
                    # Assumes determinic for now (assumes failed)
                    current_unit.status = CombatUnit.Status.SUPPRESSED
                    match gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            gs.initiative = InitiativeState.Faction.BLUE
                    current_unit.current_waypoint_id = action.interrupt_at_id
                else:
                    current_unit.current_waypoint_id = target_unit.current_waypoint_id

                # Runs the assault dice roll. Assumes determinic for now
                killed_unit: AbstractedCombatUnit
                if target_unit.status == CombatUnit.Status.SUPPRESSED:
                    gs.combat_units.pop(action.target_id)
                    killed_unit = target_unit
                else:
                    killed_unit = current_unit
                    gs.combat_units.pop(action.unit_id)
                    # Assault failed
                    match gs.initiative:
                        case InitiativeState.Faction.BLUE:
                            gs.initiative = InitiativeState.Faction.RED
                        case InitiativeState.Faction.RED:
                            gs.initiative = InitiativeState.Faction.BLUE

                for objective in gs.objectives:
                    if killed_unit.faction == objective.target_faction:
                        objective.units_destroyed_counter += 1
                return [gs]

    def get_winner(self) -> InitiativeState.Faction | None: ...

    def _get_move_interrupt(
        self,
        current_unit: AbstractedCombatUnit,
        move_to_id: int,
    ) -> int | None:
        current_waypoint = self.waypoints[current_unit.current_waypoint_id]
        for path_id in current_waypoint.movable_paths[move_to_id]:
            for enemy_unit in self.combat_units.values():
                # Add interrupt if the enemy can reactive fire it
                if enemy_unit.faction == current_unit.faction:
                    continue
                if enemy_unit.status == CombatUnit.Status.SUPPRESSED:
                    continue
                enemy_visible_nodes = self.waypoints[
                    enemy_unit.current_waypoint_id
                ].visible_nodes
                if path_id in enemy_visible_nodes:
                    return path_id
        return None
