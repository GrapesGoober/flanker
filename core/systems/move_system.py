from typing import Iterable
from core.actions import MoveActionResult
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
    def move(gs: GameState, unit_id: int, to: Vec2) -> MoveActionResult:
        """Performs move action mutation to position. May trigger reactive fire."""

        if not MoveSystem._validate_move(gs, unit_id, to):
            return MoveActionResult(is_valid=False)

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
                fire_controls = gs.get_component(spotter_id, FireControls)
                spotter_unit = gs.get_component(spotter_id, CombatUnit)
                match FireSystem.get_fire_outcome(gs, spotter_id):
                    case FireControls.Outcomes.MISS:
                        fire_controls.can_reactive_fire = False
                        continue
                    case FireControls.Outcomes.PIN:
                        unit.status = CombatUnit.Status.PINNED
                    case FireControls.Outcomes.SUPPRESS:
                        unit.status = CombatUnit.Status.SUPPRESSED
                        InitiativeSystem.set_initiative(gs, spotter_unit.faction)
                    case FireControls.Outcomes.KILL:
                        MoveSystem.update_terrain_inside(gs, unit_id, start)
                        CommandSystem.kill_unit(gs, unit_id)
                        InitiativeSystem.set_initiative(gs, spotter_unit.faction)
                return MoveActionResult(
                    is_valid=True,
                    is_interrupted=True,
                )

        MoveSystem.update_terrain_inside(gs, unit_id, start)
        return MoveActionResult(
            is_valid=True,
            is_interrupted=False,
        )

    @staticmethod
    def update_terrain_inside(gs: GameState, unit_id: int, start: Vec2) -> None:
        """Checks terrain and mutates CombatUnit's inside_terrains list."""

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        unit.inside_terrains = unit.inside_terrains or []  # Remove None
        for intersect in IntersectSystem.get(gs, start, transform.position):
            tid = intersect.terrain_id
            if tid in unit.inside_terrains:
                unit.inside_terrains.remove(tid)
            else:
                unit.inside_terrains.append(tid)
