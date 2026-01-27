from dataclasses import dataclass

from flanker_core.gamestate import GameState

from webapi.models import ActionLog


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

    @staticmethod
    def clear_logs(gs: GameState) -> None:
        if results := gs.query(_LogRecords):
            _, log_records = results[0]
            log_records.logs = []
