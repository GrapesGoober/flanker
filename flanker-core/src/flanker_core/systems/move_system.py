import math
from dataclasses import dataclass
from typing import Literal

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
class _PivotActionResult:
    """Result of a pivot action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class _GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    results: list[_MoveActionResult]


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
    def _get_interrupt_candidates(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> list[tuple[Vec2, list[int]]]:
        """Returns move interrupt points and attacker IDs"""

        spotter_candidates = list(
            FireSystem.get_spotter_candidates(gs, unit_id),
        )
        interrupt_candidates: list[tuple[Vec2, list[int]]] = []

        transform = gs.get_component(unit_id, Transform)

        for spotter_id in spotter_candidates:
            spotter_fire_controls = gs.get_component(spotter_id, FireControls)
            if not spotter_fire_controls.los_polygon:
                # LOS polygon should be generated
                LosSystem.update_los_polygon(gs, spotter_id)
                assert spotter_fire_controls.los_polygon

            # Find the interrupt position if spotted,
            # either already inside LOS or move-line crosses LOS polygon
            interrupt_pos: Vec2 | None = None
            if IntersectGetter.is_inside(
                point=transform.position,
                polygon=spotter_fire_controls.los_polygon,
            ):
                interrupt_pos = transform.position
            elif intersects := IntersectGetter.get_intersects(
                line=(transform.position, to),
                polyline=spotter_fire_controls.los_polygon,
            ):
                interrupt_pos = intersects[0]

            # Move interrupt found, add this as a candidate
            if interrupt_pos is not None:
                # If this position already exists, add a the spotter
                for existing_pos, spotters in interrupt_candidates:
                    if existing_pos == interrupt_pos:
                        spotters.append(spotter_id)
                        break
                else:  # Otherwise add a new candidate entry
                    interrupt_candidates.append((interrupt_pos, [spotter_id]))

        # Sort the intersection candidates based on distance from starting pos
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
        """
        Mutator method moves a single unit with reactive fire.
        Doesn't flip initiative.
        """

        if (reason := MoveSystem._validate_move(gs, unit_id, to)) != True:
            return reason

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_direction = (to - transform.position).normalized()

        interrupt_candidates = MoveSystem._get_interrupt_candidates(gs, unit_id, to)

        # Reset LOS polygon after move
        mover_fire_controls = gs.try_component(unit_id, FireControls)
        if mover_fire_controls:
            mover_fire_controls.los_polygon = None

        # Set orientation towards move direction
        angle_rad = math.atan2(move_direction.y, move_direction.x)
        transform.degrees = math.degrees(angle_rad)

        # In case of being interrupted, add a tiny offset to
        # prevent entity from sitting precisely on LOS polygon edge.
        # This reduces floating point sensitivity
        offset = move_direction * 1e-12

        # Track the most-severe fire outcome.
        # More severe outcomes will override this variables.
        reactive_fire_outcome: FireOutcomes | None = None

        for pos, spotter_ids in interrupt_candidates:

            # If the unit got interrupted and stopped moving,
            # subsequent spotters don't get to fire.
            if reactive_fire_outcome is not None:
                break

            # All spotters in this in candidate gets to reactive fire
            for spotter_id in spotter_ids:
                outcome = FireSystem.get_fire_outcome(gs, spotter_id)

                # Some previous fire outcomes might have killed unit,
                # so break early to prevent a non-existant entity being used.
                if not gs.try_component(unit_id, CombatUnit):
                    break

                # Apply each outcome
                match outcome:
                    case FireOutcomes.MISS:
                        # Marks the firer as NO FIRE
                        fire_controls = gs.get_component(spotter_id, FireControls)
                        fire_controls.can_reactive_fire = False
                    case FireOutcomes.PIN:
                        transform.position = pos + offset
                        # Only ACTIVE units become PINNED
                        if unit.status == CombatUnit.Status.ACTIVE:
                            unit.status = CombatUnit.Status.PINNED
                            reactive_fire_outcome = outcome
                    case FireOutcomes.SUPPRESS:
                        transform.position = pos + offset
                        # Non-suppressed becomes SUPPRESSED, otherwise KILL
                        if unit.status != CombatUnit.Status.SUPPRESSED:
                            unit.status = CombatUnit.Status.SUPPRESSED
                        else:  # Kill if already suppressed
                            CommandSystem.kill_unit(gs, unit_id)
                        reactive_fire_outcome = outcome
                    case FireOutcomes.KILL:
                        reactive_fire_outcome = outcome
                        CommandSystem.kill_unit(gs, unit_id)

        if reactive_fire_outcome is None:
            transform.position = to

        return _MoveActionResult(
            reactive_fire_outcome=reactive_fire_outcome,
        )

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

        return _GroupMoveActionResult(results)

    @staticmethod
    def pivot(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> _PivotActionResult | InvalidAction:
        """Mutator method performs pivot action with reactive fire."""

        transform = gs.get_component(unit_id, Transform)
        initial_position = transform.position

        # Cheeky implementation by having it move tiny step forward;
        # the singular move handles pivoting AND reactive fire
        move_vector = (to - transform.position).normalized() * 1e-12
        move_to = initial_position + move_vector
        result = MoveSystem._singular_move(gs, unit_id, move_to)

        # Then put it back to where it were so it's not actually moved
        transform.position = initial_position

        if isinstance(result, _MoveActionResult):
            return _PivotActionResult(result.reactive_fire_outcome)
        return result
