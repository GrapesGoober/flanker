from dataclasses import dataclass

from webapi.models.action_models import ActionLog
from webapi.models.state_models import TerrainType


@dataclass
class TerrainTypeTag:
    """Tag to store the terrain type."""

    type: TerrainType


@dataclass
class LogRecords:
    """Singleton component contains past action log snapshots."""

    logs: list[ActionLog]
