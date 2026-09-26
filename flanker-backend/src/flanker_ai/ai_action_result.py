from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.components import InitiativeState
from pydantic.dataclasses import dataclass


@dataclass
class AiActionResult[TLog]:
    faction: InitiativeState.Faction
    action: Action
    result: ActionResult
    policy_log: TLog
