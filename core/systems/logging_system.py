from dataclasses import dataclass

from core.action_models import GroupMoveActionLog, MoveActionLog
from core.gamestate import GameState

ActionLog = MoveActionLog | GroupMoveActionLog


@dataclass
class _ActionLogs:
    entries: list[ActionLog]


class LoggingSystem:
    @staticmethod
    def log(gs: GameState, result: ActionLog) -> None:
        if results := gs.query(_ActionLogs):
            _, logs = results[0]
        else:
            gs.add_entity(logs := _ActionLogs([]))

        logs.entries.append(result)

    @staticmethod
    def get_logs(gs: GameState) -> list[ActionLog]:
        if results := gs.query(_ActionLogs):
            _, logs = results[0]
        else:
            gs.add_entity(logs := _ActionLogs([]))

        return logs.entries
