from typing import Iterable
from core.action_models import (
    GroupMoveAction,
    GroupMoveActionLog,
    MoveAction,
    MoveActionLog,
    MoveActionResult,
)
from core.systems.command_system import CommandSystem
from core.components import (
    CombatUnit,
    FireControls,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.systems.fire_system import FireSystem
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.intersect_system import IntersectSystem
from core.utils.vec2 import Vec2


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def _validate_move(gs: GameState, unit_id: int, to: Vec2) -> bool:
        """Returns `True` if move action can be performed."""

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_controls = gs.get_component(unit_id, MoveControls)

        # Check game state is valid for move action
        if unit.status != CombatUnit.Status.ACTIVE:
            return False
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return False

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE
        for intersect in IntersectSystem.get(gs, transform.position, to):
            if not (intersect.terrain.flag & terrain_type):
                return False

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
    def _move_single_unit(gs: GameState, action: MoveAction) -> MoveActionResult:
        """Mutator method moves a unit with reactive fire. Doesn't flip initiative."""

        if not MoveSystem._validate_move(gs, action.unit_id, action.to):
            return MoveActionResult(is_valid=False)

        transform = gs.get_component(action.unit_id, Transform)
        unit = gs.get_component(action.unit_id, CombatUnit)
        spotter_candidates = list(FireSystem.get_spotter_candidates(gs, action.unit_id))
        start = transform.position

        # For each subdivision step of move line, check interrupt
        for step in MoveSystem._get_move_steps(transform.position, action.to):
            transform.position = step

            # Check for interrupt
            for spotter_id in spotter_candidates:
                # Validate reactive fire actors
                if not FireSystem.validate_fire_actors(gs, spotter_id, action.unit_id):
                    continue

                # Interrupt valid, perform the reactive fire
                outcome = FireSystem.get_fire_outcome(gs, spotter_id)
                match outcome:
                    case FireControls.Outcomes.MISS:
                        fire_controls = gs.get_component(spotter_id, FireControls)
                        fire_controls.can_reactive_fire = False
                        continue
                    case FireControls.Outcomes.PIN:
                        unit.status = CombatUnit.Status.PINNED
                        MoveSystem.update_terrain_inside(gs, action.unit_id, start)
                    case FireControls.Outcomes.SUPPRESS:
                        unit.status = CombatUnit.Status.SUPPRESSED
                        MoveSystem.update_terrain_inside(gs, action.unit_id, start)
                    case FireControls.Outcomes.KILL:
                        CommandSystem.kill_unit(gs, action.unit_id)
                return MoveActionResult(
                    is_valid=True,
                    reactive_fire_outcome=outcome,
                )

        MoveSystem.update_terrain_inside(gs, action.unit_id, start)
        return MoveActionResult(is_valid=True)

    @staticmethod
    def move(gs: GameState, action: MoveAction) -> MoveActionResult:
        """Mutator method performs move action with reactive fire."""

        result = MoveSystem._move_single_unit(gs, action)
        if result.reactive_fire_outcome in (
            FireControls.Outcomes.SUPPRESS,
            FireControls.Outcomes.KILL,
        ):
            InitiativeSystem.flip_initiative(gs)

        # TODO: implement core-level logging here
        return result

    @staticmethod
    def group_move(gs: GameState, action: GroupMoveAction) -> GroupMoveActionLog:
        """Mutator method performs group move action with reactive fire."""

        logs: list[MoveActionLog] = []
        interrupt_count = 0
        # TODO: group move validation
        for move in action.moves:
            result = MoveSystem._move_single_unit(gs, move)
            if result.reactive_fire_outcome in (
                FireControls.Outcomes.SUPPRESS,
                FireControls.Outcomes.KILL,
            ):
                interrupt_count += 1

        if interrupt_count >= len(action.moves):
            InitiativeSystem.flip_initiative(gs)

        # TODO: implement core-level logging here
        return GroupMoveActionLog(logs)

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
