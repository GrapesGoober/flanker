from dataclasses import dataclass
from backend.models import ActionLog
from core.gamestate import GameState


@dataclass
class _LogRecords:
    logs: list[ActionLog]


class LoggingService:

    @staticmethod
    def log(gs: GameState, log: ActionLog) -> None:
        if results := gs.query(_LogRecords):
            _, log_records = results[0]
        else:
            gs.add_entity(log_records := _LogRecords([]))

        log_records.logs.append(log)

    @staticmethod
    def get_logs(gs: GameState) -> list[ActionLog]:
        if results := gs.query(_LogRecords):
            _, log_records = results[0]
            return log_records.logs
        return []
