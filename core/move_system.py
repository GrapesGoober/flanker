from dataclasses import dataclass
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
    def move(gs: GameState, unit_id: int, to: Vec2) -> MoveActionResult:
        """Performs move action to position; may trigger reactive fire."""

        # Check move action is valid
        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_controls = gs.get_component(unit_id, MoveControls)

        if unit.status != CombatUnit.Status.ACTIVE:
            return MoveActionResult(is_valid=False)
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return MoveActionResult(is_valid=False)

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE

        for intersect in IntersectSystem.get(gs, transform.position, to):
            if not (intersect.terrain.flag & terrain_type):
                return MoveActionResult(is_valid=False)

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
            # TODO: for fire reaction, should support multiple shooter
            for spotter_id in spotter_candidates:
                # Interrupt valid, perform the fire action
                fire_result = FireSystem.fire(
                    gs=gs,
                    attacker_id=spotter_id,
                    target_id=unit_id,
                    is_reactive=True,
                )
                if fire_result.is_hit:
                    if fire_result.outcome != FireControls.Outcomes.KILL:
                        MoveSystem.update_terrain_inside(gs, unit_id, start)
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
