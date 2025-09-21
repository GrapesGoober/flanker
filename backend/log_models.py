from enum import Enum
from pydantic import BaseModel
from backend.models import (
    AssaultActionRequest,
    FireActionRequest,
    MoveActionRequest,
    CombatUnitsViewState,
)
from core.systems.assault_system import AssaultActionResult
from core.systems.fire_system import FireActionResult
from core.systems.move_system import MoveActionResult


class ActionType(str, Enum):
    MOVE = "move"
    FIRE = "fire"
    ASSAULT = "assault"


class MoveActionLog(BaseModel):
    type: ActionType = ActionType.MOVE
    body: MoveActionRequest
    result: MoveActionResult
    unit_state: CombatUnitsViewState


class FireActionLog(BaseModel):
    type: ActionType = ActionType.FIRE
    body: FireActionRequest
    result: FireActionResult
    unit_state: CombatUnitsViewState


class AssaultActionLog(BaseModel):
    type: ActionType = ActionType.ASSAULT
    body: AssaultActionRequest
    result: AssaultActionResult
    unit_state: CombatUnitsViewState


ActionLog = MoveActionLog | FireActionLog | AssaultActionLog


class LogFile(BaseModel):
    actions: list[ActionLog]
