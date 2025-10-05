from typing import Iterable, Literal
from core.action_models import InvalidActionTypes
from core.systems.command_system import CommandSystem
from core.components import (
    CombatUnit,
    FireControls,
    FireOutcomes,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.systems.fire_system import FireSystem
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.intersect_system import IntersectSystem
from core.utils.vec2 import Vec2
from dataclasses import dataclass


@dataclass
class MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    moveActionLogs: list[MoveActionResult]


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def _validate_move(
        gs: GameState, unit_id: int, to: Vec2
    ) -> Literal[True] | InvalidActionTypes:
        """Returns `True` if move action can be performed."""

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_controls = gs.get_component(unit_id, MoveControls)

        # Check game state is valid for move action
        if unit.status != CombatUnit.Status.ACTIVE:
            return InvalidActionTypes.BAD_INITIATIVE
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return InvalidActionTypes.BAD_INITIATIVE

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE
        for intersect in IntersectSystem.get(gs, transform.position, to):
            if not (intersect.terrain.flag & terrain_type):
                return InvalidActionTypes.BAD_COORDS

        return True

    @staticmethod
    def _get_move_steps(start: Vec2, to: Vec2, step_size: int = 1) -> Iterable[Vec2]:
        """Yields position from `start` to `to` in increments of `step_size`."""
        current = start
        direction = (to - start).normalized()
        total_length = (to - start).length()
        steps = int(total_length / step_size) + 1

        for i in range(steps):
            step = min(step_size, total_length - i * step_size)
            current = current + direction * step
            yield current

    @staticmethod
    def _singular_move(
        gs: GameState, unit_id: int, to: Vec2
    ) -> MoveActionResult | InvalidActionTypes:
        """Mutator method moves a single unit with reactive fire. Doesn't flip initiative."""

        if (reason := MoveSystem._validate_move(gs, unit_id, to)) != True:
            return reason

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        spotter_candidates = list(FireSystem.get_spotter_candidates(gs, unit_id))
        start = transform.position

        # For each subdivision step of move line, check interrupt
        for step in MoveSystem._get_move_steps(transform.position, to):
            transform.position = step

            # Check for interrupt
            for spotter_id in spotter_candidates:
                # Validate reactive fire actors
                if not FireSystem.validate_fire_actors(gs, spotter_id, unit_id):
                    continue

                # Interrupt valid, perform the reactive fire
                outcome = FireSystem.get_fire_outcome(gs, spotter_id)
                match outcome:
                    case FireOutcomes.MISS:
                        fire_controls = gs.get_component(spotter_id, FireControls)
                        fire_controls.can_reactive_fire = False
                        continue
                    case FireOutcomes.PIN:
                        unit.status = CombatUnit.Status.PINNED
                        MoveSystem.update_terrain_inside(gs, unit_id, start)
                    case FireOutcomes.SUPPRESS:
                        unit.status = CombatUnit.Status.SUPPRESSED
                        MoveSystem.update_terrain_inside(gs, unit_id, start)
                    case FireOutcomes.KILL:
                        CommandSystem.kill_unit(gs, unit_id)
                return MoveActionResult(
                    reactive_fire_outcome=outcome,
                )

        MoveSystem.update_terrain_inside(gs, unit_id, start)
        return MoveActionResult()

    @staticmethod
    def move(
        gs: GameState, unit_id: int, to: Vec2
    ) -> MoveActionResult | InvalidActionTypes:
        """Mutator method performs move action with reactive fire."""

        result = MoveSystem._singular_move(gs, unit_id, to)
        if not isinstance(result, MoveActionResult):
            return result
        if result.reactive_fire_outcome in (
            FireOutcomes.SUPPRESS,
            FireOutcomes.KILL,
        ):
            InitiativeSystem.flip_initiative(gs)

        return result

    @staticmethod
    def group_move(
        gs: GameState, moves: list[tuple[int, Vec2]]
    ) -> GroupMoveActionResult | InvalidActionTypes:
        """Mutator method performs group move action with reactive fire."""

        logs: list[MoveActionResult] = []
        interrupt_count = 0
        # TODO: group move validation
        for unit_id, to in moves:
            result = MoveSystem._singular_move(gs, unit_id, to)
            if not isinstance(result, MoveActionResult):
                return result
            if result.reactive_fire_outcome in (
                FireOutcomes.SUPPRESS,
                FireOutcomes.KILL,
            ):
                interrupt_count += 1

        if interrupt_count >= len(moves):
            InitiativeSystem.flip_initiative(gs)

        return GroupMoveActionResult(logs)

    @staticmethod
    def update_terrain_inside(gs: GameState, unit_id: int, start: Vec2) -> None:
        """Mutator method that rechecks and updates CombatUnit's inside_terrains."""

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        unit.inside_terrains = unit.inside_terrains or []  # Remove None
        for intersect in IntersectSystem.get(gs, start, transform.position):
            tid = intersect.terrain_id
            if tid in unit.inside_terrains:
                unit.inside_terrains.remove(tid)
            else:
                unit.inside_terrains.append(tid)
