import math
from dataclasses import dataclass
from typing import Iterable, Literal

from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.intersect_system import IntersectSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter


@dataclass
class _MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class _GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    results: list[_MoveActionResult]


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    # half-angle of forward field-of-view cone used by both firing and
    # reactive-fire rules. 45° each side is the established game rule that
    # also appears in :class:`FireSystem`.
    FOV_HALF_ANGLE: float = 45.0

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
            if not intersect.terrain.flag & terrain_type:
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
    def _get_segment_param(
        start: Vec2,
        end: Vec2,
        point: Vec2,
    ) -> float:
        """Return normalized segment parameter t in [0,1] for `point` on `start->end`."""
        segment = end - start
        segment_len_sq = segment.dot(segment)
        if segment_len_sq == 0:
            return 0.0
        return max(0.0, min(1.0, (point - start).dot(segment) / segment_len_sq))

    @staticmethod
    def _get_first_visible_in_fov_point(
        start: Vec2,
        to: Vec2,
        spotter_pos: Vec2,
        spotter_heading: float,
        los_polygon: list[Vec2] | None,
    ) -> Vec2 | None:
        """Find the earliest point on move segment where both LOS and FOV are valid.

        This solves edge cases where checking only one LOS intersection point misses
        paths that enter the spotter's FOV cone later while already inside LOS.
        """

        move = to - start
        move_len_sq = move.dot(move)

        has_polygon = los_polygon is not None and len(los_polygon) > 2

        # Collect transition parameters where LOS/FOV truth value may change.
        t_values = [0.0, 1.0]

        if has_polygon and los_polygon:
            for point in IntersectGetter.get_intersects(
                line=(start, to),
                polyline=los_polygon,
            ):
                t_values.append(MoveSystem._get_segment_param(start, to, point))

        # Intersections with left/right FOV boundary rays.
        # These are where the movement crosses into/out of the cone.
        heading_rad = math.radians(spotter_heading)
        base_dir = Vec2(math.cos(heading_rad), math.sin(heading_rad))
        half_rad = math.radians(MoveSystem.FOV_HALF_ANGLE)
        ray_scale = max((to - start).length(), 1000.0) * 4.0
        for boundary_dir in (base_dir.rotated(half_rad), base_dir.rotated(-half_rad)):
            ray_end = spotter_pos + boundary_dir * ray_scale
            for point in IntersectGetter.get_intersects(
                line=(start, to),
                polyline=[spotter_pos, ray_end],
            ):
                t_values.append(MoveSystem._get_segment_param(start, to, point))

        # De-duplicate sorted transition points.
        t_values = sorted(t_values)
        unique_t: list[float] = []
        for t in t_values:
            if not unique_t or abs(t - unique_t[-1]) > 1e-9:
                unique_t.append(t)

        if move_len_sq == 0:
            point = start
            in_los = (
                IntersectGetter.is_inside(point=point, polygon=los_polygon)
                if has_polygon and los_polygon
                else True
            )
            in_fov = LosSystem.is_in_fov(
                spotter_pos,
                spotter_heading,
                point,
                MoveSystem.FOV_HALF_ANGLE,
            )
            if in_los and in_fov:
                return point
            return None

        # Evaluate each interval; if valid there, earliest valid point is at
        # interval start (a transition t value).
        for idx, t_start in enumerate(unique_t[:-1]):
            t_end = unique_t[idx + 1]
            t_mid = (t_start + t_end) * 0.5
            point_mid = start + move * t_mid

            in_los_mid = (
                IntersectGetter.is_inside(point=point_mid, polygon=los_polygon)
                if has_polygon and los_polygon
                else True
            )
            in_fov_mid = LosSystem.is_in_fov(
                spotter_pos,
                spotter_heading,
                point_mid,
                MoveSystem.FOV_HALF_ANGLE,
            )

            if not (in_los_mid and in_fov_mid):
                continue

            candidate = start + move * t_start
            return candidate

        # Also check exact endpoint.
        endpoint = to
        in_los_end = (
            IntersectGetter.is_inside(point=endpoint, polygon=los_polygon)
            if has_polygon and los_polygon
            else True
        )
        in_fov_end = LosSystem.is_in_fov(
            spotter_pos,
            spotter_heading,
            endpoint,
            MoveSystem.FOV_HALF_ANGLE,
        )
        if in_los_end and in_fov_end:
            return endpoint

        return None

    @staticmethod
    def get_interrupt_candidates(
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
            spotter_transform = gs.get_component(spotter_id, Transform)

            spotter_fire_controls = gs.get_component(spotter_id, FireControls)
            if not spotter_fire_controls.los_polygon:
                LosSystem.update_los_polygon(gs, spotter_id)
                # LOS polygon should be generated
                assert spotter_fire_controls.los_polygon

            candidate_point = MoveSystem._get_first_visible_in_fov_point(
                start=transform.position,
                to=to,
                spotter_pos=spotter_transform.position,
                spotter_heading=spotter_transform.degrees,
                los_polygon=spotter_fire_controls.los_polygon,
            )

            if candidate_point is None:
                continue

            interrupt_candidates.append((candidate_point, spotter_id))
            continue

        # Sort the intersection candidates based distance from moving unit
        interrupt_candidates = sorted(
            interrupt_candidates,
            key=lambda intersect: (intersect[0] - transform.position).length(),
        )

        return interrupt_candidates

    @staticmethod
    def _get_interrupt_candidates(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> list[tuple[Vec2, int]]:
        """Backward-compatible wrapper. Prefer `get_interrupt_candidates`."""
        return MoveSystem.get_interrupt_candidates(gs, unit_id, to)

    @staticmethod
    def _singular_move(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> _MoveActionResult | InvalidAction:
        """Mutator method moves a single unit with reactive fire. Doesn't flip initiative."""

        reason = MoveSystem._validate_move(gs, unit_id, to)
        if reason is not True:
            return reason

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)

        # pivot unit to face direction of travel before moving
        direction = (to - transform.position).normalized()
        # compute heading in degrees, similar to player controller
        # compute heading, avoid division by zero
        if direction.x == 0 and direction.y == 0:
            heading = 0
        else:
            heading = (180 / math.pi) * math.atan2(direction.y, direction.x)
        if heading < 0:
            heading += 360
        transform.degrees = heading

        interrupt_candidates = MoveSystem.get_interrupt_candidates(gs, unit_id, to)

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

        results: list[_MoveActionResult] = []
        interrupt_count = 0
        # NOTE: group move validation remains TODO
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

        return _GroupMoveActionResult(results)
