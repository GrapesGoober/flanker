from dataclasses import dataclass
from core.command_system import CommandSystem
from core.components import (
    CombatUnit,
    FireControls,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.initiative_system import InitiativeSystem
from core.intersect_system import IntersectSystem
from core.utils.vec2 import Vec2


@dataclass
class MoveActionResult:
    """Result of a move action whether is valid or interrupted."""

    is_valid: bool
    is_interrupted: bool = False


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def _validate_move(gs: GameState, unit_id: int, to: Vec2) -> bool:

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
    def move(gs: GameState, unit_id: int, to: Vec2) -> MoveActionResult:
        """Performs move action to position; may trigger reactive fire."""

        if not MoveSystem._validate_move(gs, unit_id, to):
            return MoveActionResult(is_valid=False)

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        spotter_candidates = list(FireSystem.get_spotters(gs, unit_id))

        # For each subdivision step of move line, check interrupt
        STEP_SIZE = 1
        start = transform.position
        length = (to - transform.position).length()
        direction = (to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            # Use min(); last move step will be smaller than step size
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step

            # Check for interrupt
            for spotter_id in spotter_candidates:

                # Validate reactive fire
                fire_controls = gs.get_component(spotter_id, FireControls)
                spotter_unit = gs.get_component(spotter_id, CombatUnit)
                if not fire_controls.can_reactive_fire:
                    continue
                if not FireSystem.validate_fire_action(
                    gs, spotter_id, unit_id, is_reactive=True
                ):
                    continue

                # Interrupt valid, perform the reactive fire
                match FireSystem.get_fire_outcome(gs, spotter_id):
                    case FireControls.Outcomes.MISS:
                        fire_controls.can_reactive_fire = False
                    case FireControls.Outcomes.PIN:
                        unit.status = CombatUnit.Status.PINNED
                        return MoveActionResult(
                            is_valid=True,
                            is_interrupted=True,
                        )
                    case FireControls.Outcomes.SUPPRESS:
                        unit.status = CombatUnit.Status.SUPPRESSED
                        InitiativeSystem.set_initiative(gs, spotter_unit.faction)
                        return MoveActionResult(
                            is_valid=True,
                            is_interrupted=True,
                        )
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
        """Updates CombatUnit's inside_terrains list."""

        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        unit.inside_terrains = unit.inside_terrains or []  # Remove None
        for intersect in IntersectSystem.get(gs, start, transform.position):
            tid = intersect.terrain_id
            if tid in unit.inside_terrains:
                unit.inside_terrains.remove(tid)
            else:
                unit.inside_terrains.append(tid)
