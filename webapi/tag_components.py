from dataclasses import dataclass

from webapi.models import TerrainModel


@dataclass
class TerrainTypeTag:
    """Tag to store the terrain type."""

    type: TerrainModel.Types
