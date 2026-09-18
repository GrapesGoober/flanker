from typing import Literal
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.actions import MoveActionResult, PivotActionResult
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    MapBoundary,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.utils.intersect_utils import IntersectUtils
from flanker_core.utils.transform_utils import TransformUtils

# This is a bandaid fix for LOS polygon imprecision
_MOVE_INTERRUPT_ATOL = 5


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def validate_move(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> Literal[True] | InvalidAction:
        """Returns `True` if move action can be performed."""
        transform = gs.get_component(unit_id, Transform)
        move_controls = gs.get_component(unit_id, MoveControls)
        move_unit = gs.get_component(unit_id, CombatUnit)

        # Check game state is valid for move action
        if move_unit.status != CombatUnit.Status.ACTIVE:
            return InvalidAction.INACTIVE_UNIT
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return InvalidAction.NO_INITIATIVE

        # Check move action though correct terrain type
        movable_mask = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                movable_mask = TerrainFeature.Flag.WALKABLE

        invalid_obstacles: list[list[Vec2]] = []
        for _, boundary in gs.query(MapBoundary):
            vertices = list(boundary.vertices) + [boundary.vertices[0]]
            invalid_obstacles.append(vertices)

        for _, terrain, terrain_transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & movable_mask) != 0:
                continue
            vertices = TransformUtils.apply(terrain.vertices, terrain_transform)
            if terrain.is_closed_loop:
                vertices.append(vertices[0])
            invalid_obstacles.append(vertices)

        # Check if doesn't move through invalid obstacles
        for obstacle in invalid_obstacles:
            intersections = IntersectUtils.get_intersects(
                line=(transform.position, to),
                polyline=obstacle,
            )
            if len(intersections) != 0:
                return InvalidAction.BAD_COORDS

        return True

    @staticmethod
    def get_interrupt_candidates(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> list[tuple[Vec2, list[UUID]]]:
        """Returns move interrupt candidate points and reactive firer IDs"""

        firer_candidates = list(
            FireSystem.get_reactive_fire_candidates(gs, unit_id),
        )
        interrupt_candidates: list[tuple[Vec2, list[UUID]]] = []

        transform = gs.get_component(unit_id, Transform)

        for firer_id in firer_candidates:
            interrupt_pos = LosSystem.get_los_from_line(
                gs=gs,
                spotter_id=firer_id,
                line_from=transform.position,
                line_to=to,
            )

            # Move interrupt found, add this as a candidate
            if interrupt_pos is not None:
                # If this position already exists, add a the spotter
                for existing_pos, firer_ids in interrupt_candidates:
                    if existing_pos.is_close(
                        interrupt_pos, abs_tol=_MOVE_INTERRUPT_ATOL
                    ):
                        firer_ids.append(firer_id)
                        break
                else:  # Otherwise add a new candidate entry
                    interrupt_candidates.append((interrupt_pos, [firer_id]))

        # Sort the intersection candidates based on distance from starting pos
        interrupt_candidates = sorted(
            interrupt_candidates,
            key=lambda intersect: (intersect[0] - transform.position).length(),
        )

        return interrupt_candidates

    @staticmethod
    def _atomic_move(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> MoveActionResult | InvalidAction:
        """
        Atomic move operation for a unit. Orients and moves unit
        in that direction with reactive fire. Doesn't flip initiative.
        """
        if (reason := MoveSystem.validate_move(gs, unit_id, to)) != True:
            return reason

        transform = gs.get_component(unit_id, Transform)

        interrupt_candidates = MoveSystem.get_interrupt_candidates(gs, unit_id, to)

        # Count stall if no possibility of reactive fires
        unit = gs.get_component(unit_id, CombatUnit)
        if len(interrupt_candidates) == 0:
            ObjectiveSystem.count_stall(gs, unit.faction)
        else:
            ObjectiveSystem.reset_stall(gs, unit.faction)

        # Reset fire effect if exist
        fire_controls = gs.try_component(unit_id, FireControls)
        if fire_controls != None:
            fire_controls.firing_at = None

        # Set orientation towards move direction
        transform.degrees = transform.position.angle_to(to)

        # Track the most-severe fire outcome.
        # More severe outcomes will override this variables.
        reactive_fire_outcomes: list[FireOutcomes] = []
        move_interrupted: bool = False

        for pos, firer_ids in interrupt_candidates:

            # If the unit got interrupted and stopped moving,
            # subsequent spotters don't get to fire.
            if move_interrupted == True:
                break

            # All spotters in this in candidate gets to reactive fire
            for firer_id in firer_ids:
                transform.position = pos

                # Some previous fire outcomes might have killed unit,
                # so break early to prevent a non-existant entity being used.
                if gs.try_component(unit_id, CombatUnit) is None:
                    break

                # Validate sight before reactively firing
                if FireSystem.validate_fire_actors(gs, firer_id, unit_id) != None:
                    continue

                # Apply reactive fire outcome
                outcome = FireSystem.get_fire_outcome(gs, firer_id)
                FireSystem.apply_fire_outcome(
                    gs,
                    attacker_id=firer_id,
                    target_id=unit_id,
                    fire_outcome=outcome,
                )
                reactive_fire_outcomes.append(outcome)

                # If reactively fired upon, it stops at that position
                if outcome in [
                    FireOutcomes.PIN,
                    FireOutcomes.SUPPRESS,
                    FireOutcomes.KILL,
                ]:
                    move_interrupted = True

        # If not being reactive fired upon, it moves to target position
        if move_interrupted == False:
            transform.position = to

        return MoveActionResult(
            move_interrupted=move_interrupted,
            reactive_fire_outcomes=reactive_fire_outcomes,
        )

    @staticmethod
    def move(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> MoveActionResult | InvalidAction:
        """Performs a complete move action with reactive fire."""

        result = MoveSystem._atomic_move(gs, unit_id, to)
        if not isinstance(result, MoveActionResult):
            return result
        # If there are any SUPPRESS or KILL reactive fires,
        # the initiative is lost.
        if {
            FireOutcomes.SUPPRESS,
            FireOutcomes.KILL,
        } & set(result.reactive_fire_outcomes):
            InitiativeSystem.flip_initiative(gs)

        return result

    @staticmethod
    def pivot(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> PivotActionResult | InvalidAction:
        """Performs a complete pivot action with reactive fire."""

        transform = gs.get_component(unit_id, Transform)
        initial_position = transform.position

        # Cheeky implementation by having it move tiny step forward;
        # the singular move handles pivoting AND reactive fire
        move_vector = (to - transform.position).normalized() * 1e-12
        move_to = initial_position + move_vector
        result = MoveSystem._atomic_move(gs, unit_id, move_to)

        if isinstance(result, InvalidAction):
            return result

        # If there are any SUPPRESS or KILL reactive fires,
        # the initiative is lost.
        if {
            FireOutcomes.SUPPRESS,
            FireOutcomes.KILL,
        } & set(result.reactive_fire_outcomes):
            InitiativeSystem.flip_initiative(gs)

        # Then put it back to where it were so it's not actually moved
        transform.position = initial_position

        return PivotActionResult(result.reactive_fire_outcomes)
