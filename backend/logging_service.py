from backend.log_models import ActionLog


class LoggingService:
    def __init__(self) -> None:
        self.logs: list[ActionLog] = []

    def append(self, log: ActionLog): ...
