from dataclasses import dataclass
from typing import Iterable, Literal

from core.gamestate import GameState
from core.models.components import (
    CombatUnit,
    FireControls,
    MoveControls,
    TerrainFeature,
    Transform,
)
from core.models.outcomes import FireOutcomes, InvalidAction
from core.models.vec2 import Vec2
from core.systems.command_system import CommandSystem
from core.systems.fire_system import FireSystem
from core.systems.initiative_system import InitiativeSystem
from core.systems.intersect_system import IntersectSystem
from core.systems.los_system import IntersectGetter, LosSystem


@dataclass
class _MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class _GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    moveActionLogs: list[_MoveActionResult]


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def _validate_move(
        gs: GameState, unit_id: int, to: Vec2
    ) -> Literal[True] | InvalidAction:
        """Returns `True` if move action can be performed."""

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_controls = gs.get_component(unit_id, MoveControls)

        # Check game state is valid for move action
        if unit.status != CombatUnit.Status.ACTIVE:
            return InvalidAction.INACTIVE_UNIT
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return InvalidAction.NO_INITIATIVE

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE
        for intersect in IntersectSystem.get(gs, transform.position, to):
            if not (intersect.terrain.flag & terrain_type):
                return InvalidAction.BAD_COORDS

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
    def _get_interrupt_candidates(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> list[tuple[Vec2, int]]:
        spotter_candidates = list(
            FireSystem.get_spotter_candidates(gs, unit_id),
        )
        interrupt_candidates: list[tuple[Vec2, int]] = []

        transform = gs.get_component(unit_id, Transform)

        for spotter_id in spotter_candidates:
            spotter_fire_controls = gs.get_component(spotter_id, FireControls)
            if not spotter_fire_controls.los_polygon:
                LosSystem.update_los_polygon(gs, spotter_id)
                # LOS polygon should be generated
                assert spotter_fire_controls.los_polygon

            # Check if target is in line of sight
            if IntersectGetter.is_inside(
                point=transform.position,
                vertices=spotter_fire_controls.los_polygon,
            ):
                interrupt_candidates.append((transform.position, spotter_id))
                continue
            if intersects := IntersectGetter.get_intersects(
                line=(transform.position, to),
                vertices=spotter_fire_controls.los_polygon,
            ):
                interrupt_candidates.append((intersects[0], spotter_id))
                continue

        # Sort the intersection candidates based distance from moving unit
        interrupt_candidates = sorted(
            interrupt_candidates,
            key=lambda intersect: (intersect[0] - transform.position).length(),
        )

        return interrupt_candidates

    @staticmethod
    def _singular_move(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> _MoveActionResult | InvalidAction:
        """Mutator method moves a single unit with reactive fire. Doesn't flip initiative."""

        if (reason := MoveSystem._validate_move(gs, unit_id, to)) != True:
            return reason

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)

        interrupt_candidates = MoveSystem._get_interrupt_candidates(gs, unit_id, to)

        # Tiny offset to prevent entity from sitting precisely on LOS polygon edge
        # This reduces floating point sensitivity
        offset = (to - transform.position).normalized() * 1e-12

        # Loop through each interrupt candidate point to apply move interrupt
        for interrupt_pos, spotter_id in interrupt_candidates:
            outcome = FireSystem.get_fire_outcome(gs, spotter_id)
            match outcome:
                case FireOutcomes.MISS:
                    fire_controls = gs.get_component(spotter_id, FireControls)
                    fire_controls.can_reactive_fire = False
                    continue
                case FireOutcomes.PIN:
                    unit.status = CombatUnit.Status.PINNED
                    transform.position = interrupt_pos + offset
                case FireOutcomes.SUPPRESS:
                    unit.status = CombatUnit.Status.SUPPRESSED
                    transform.position = interrupt_pos + offset
                case FireOutcomes.KILL:
                    CommandSystem.kill_unit(gs, unit_id)
            return _MoveActionResult(
                reactive_fire_outcome=outcome,
            )

        transform.position = to
        return _MoveActionResult()

    @staticmethod
    def move(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> _MoveActionResult | InvalidAction:
        """Mutator method performs move action with reactive fire."""

        result = MoveSystem._singular_move(gs, unit_id, to)
        if not isinstance(result, _MoveActionResult):
            return result
        if result.reactive_fire_outcome in (
            FireOutcomes.SUPPRESS,
            FireOutcomes.KILL,
        ):
            InitiativeSystem.flip_initiative(gs)

        return result

    @staticmethod
    def group_move(
        gs: GameState,
        moves: list[tuple[int, Vec2]],
    ) -> _GroupMoveActionResult | InvalidAction:
        """Mutator method performs group move action with reactive fire."""

        logs: list[_MoveActionResult] = []
        interrupt_count = 0
        # TODO: group move validation
        for unit_id, to in moves:
            result = MoveSystem._singular_move(gs, unit_id, to)
            if not isinstance(result, _MoveActionResult):
                return result
            if result.reactive_fire_outcome in (
                FireOutcomes.SUPPRESS,
                FireOutcomes.KILL,
            ):
                interrupt_count += 1

        if interrupt_count >= len(moves):
            InitiativeSystem.flip_initiative(gs)

        return _GroupMoveActionResult(logs)
