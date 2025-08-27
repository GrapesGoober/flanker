from backend.log_models import ActionLog

logs: list[ActionLog] = []


class LoggingService:

    @staticmethod
    def log(log: ActionLog):
        logs.append(log)
