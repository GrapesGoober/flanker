from typing import Iterable, Literal
from core.action_models import (
    GroupMoveAction,
    GroupMoveActionResult,
    InvalidActionTypes,
    MoveAction,
    MoveActionResult,
)
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
from core.systems.los_system import IntersectGetter
from core.utils.vec2 import Vec2
from core.systems.los_system import LosSystem


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
            return InvalidActionTypes.INACTIVE_UNIT
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return InvalidActionTypes.NO_INITIATIVE

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
        gs: GameState, action: MoveAction
    ) -> MoveActionResult | InvalidActionTypes:
        """Mutator method moves a single unit with reactive fire. Doesn't flip initiative."""

        if (reason := MoveSystem._validate_move(gs, action.unit_id, action.to)) != True:
            return reason

        transform = gs.get_component(action.unit_id, Transform)
        unit = gs.get_component(action.unit_id, CombatUnit)
        spotter_candidates = list(
            FireSystem.get_spotter_candidates(gs, action.unit_id),
        )
        interrupt_candidates: list[tuple[Vec2, int]] = []
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
                line=(transform.position, action.to),
                vertices=spotter_fire_controls.los_polygon,
            ):
                interrupt_candidates.append((intersects[0], spotter_id))
                continue

        # Sort the intersection candidates based distance from moving unit
        interrupt_candidates = sorted(
            interrupt_candidates,
            key=lambda intersect: (intersect[0] - transform.position).length(),
        )

        # Tiny offset to prevent entity from sitting precisely on LOS polygon edge
        # This reduces likelyhood of floating point sensitivity
        offset = (action.to - transform.position).normalized() * 1e-12

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
                    CommandSystem.kill_unit(gs, action.unit_id)
            return MoveActionResult(
                reactive_fire_outcome=outcome,
            )

        transform.position = action.to
        return MoveActionResult()

    @staticmethod
    def move(
        gs: GameState, action: MoveAction
    ) -> MoveActionResult | InvalidActionTypes:
        """Mutator method performs move action with reactive fire."""

        result = MoveSystem._singular_move(gs, action)
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
        gs: GameState, action: GroupMoveAction
    ) -> GroupMoveActionResult | InvalidActionTypes:
        """Mutator method performs group move action with reactive fire."""

        logs: list[MoveActionResult] = []
        interrupt_count = 0
        # TODO: group move validation
        for move in action.moves:
            result = MoveSystem._singular_move(gs, move)
            if not isinstance(result, MoveActionResult):
                return result
            if result.reactive_fire_outcome in (
                FireOutcomes.SUPPRESS,
                FireOutcomes.KILL,
            ):
                interrupt_count += 1

        if interrupt_count >= len(action.moves):
            InitiativeSystem.flip_initiative(gs)

        return GroupMoveActionResult(logs)
