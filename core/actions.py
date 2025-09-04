from dataclasses import dataclass
from core.components import FireControls
from core.gamestate import GameState
from core.systems.fire_system import FireSystem
from core.systems.intersect_system import Transform
from core.systems.move_system import InitiativeSystem, MoveSystem
from core.tests.test_los import LosSystem
from core.utils.vec2 import Vec2


@dataclass
class MoveAction:
    unit_id: int
    to: Vec2


@dataclass
class MoveActionInterrupt:
    spotter_id: int
    interrupt_result: FireControls.Outcomes


@dataclass
class FireAction:
    unit_id: int
    target_id: int


@dataclass
class AssaultAction:
    unit_id: int
    target_id: int


@dataclass
class MoveActionLog:
    action: MoveAction
    is_valid: bool
    interrupt: MoveActionInterrupt | None = None


class ActionHandler:

    @staticmethod
    def move(gs: GameState, action: MoveAction) -> MoveActionLog:
        if not InitiativeSystem.has_initiative(gs, action.unit_id):
            return MoveActionLog(action, is_valid=False)

        if not MoveSystem.is_move_valid(gs, action.unit_id, action.to):
            return MoveActionLog(action, is_valid=False)

        transform = gs.get_component(action.unit_id, Transform)
        start = transform.position
        spotter_candidates = list(FireSystem.get_spotters(gs, action.unit_id))
        for move_step in MoveSystem.get_move_steps(gs, action.unit_id, action.to):
            # Check for interrupt
            # TODO: for fire reaction, should support multiple shooter
            for spotter_id in spotter_candidates:
                if not LosSystem.check(gs, spotter_id, move_step):
                    continue
                # Interrupt valid, perform the fire action
                fire_result = FireSystem.fire(
                    gs=gs,
                    attacker_id=spotter_id,
                    target_id=action.unit_id,
                    is_reactive=True,
                )
                if fire_result.is_hit and fire_result.outcome != None:
                    if fire_result.outcome != FireControls.Outcomes.KILL:
                        transform.position = move_step
                        MoveSystem.update_terrain_inside(gs, action.unit_id, start)
                    return MoveActionLog(
                        action,
                        is_valid=True,
                        interrupt=MoveActionInterrupt(spotter_id, fire_result.outcome),
                    )
        transform.position = action.to
        MoveSystem.update_terrain_inside(gs, action.unit_id, start)
        return MoveActionLog(
            action,
            is_valid=True,
            interrupt=None,
        )

    @staticmethod
    def fire(gs: GameState, action: FireAction) -> None: ...

    @staticmethod
    def assault(gs: GameState, action: AssaultAction) -> None: ...
