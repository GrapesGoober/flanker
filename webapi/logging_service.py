from flanker_core.gamestate import GameState

from webapi.models import ActionLog
from webapi.tag_components import LogRecords


class LoggingService:

    @staticmethod
    def log(gs: GameState, log: ActionLog) -> None:
        if results := gs.query(LogRecords):
            _, log_records = results[0]
        else:
            gs.add_entity(log_records := LogRecords([]))

        log_records.logs.append(log)

    @staticmethod
    def get_logs(gs: GameState) -> list[ActionLog]:
        if results := gs.query(LogRecords):
            _, log_records = results[0]
            return log_records.logs
        return []

    @staticmethod
    def clear_logs(gs: GameState) -> None:
        if results := gs.query(LogRecords):
            _, log_records = results[0]
            log_records.logs = []
