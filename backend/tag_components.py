from dataclasses import dataclass

from backend.models import TerrainModel


@dataclass
class PlayerFactionTag:
    """Tag a faction as a player faction."""

    ...


@dataclass
class OpponentFactionTag:
    """Tag a faction as a player faction."""

    ...


@dataclass
class TerrainTypeTag:
    """Tag to store the terrain type."""

    type: TerrainModel.Types
