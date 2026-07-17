from dataclasses import dataclass

from webapi.models import ActionLog, TerrainModel


@dataclass
class TerrainTypeTag:
    """Tag to store the terrain type."""

    type: TerrainModel.Types


@dataclass
class LogRecords:
    logs: list[ActionLog]
