from dataclasses import dataclass, is_dataclass
from inspect import isclass
from typing import Any
from backend import CombatUnitService
from backend.terrain_service import TerrainService
from core.gamestate import GameState
from core import components


@dataclass
class SceneContext:
    """Holds the game state and faction IDs for a scene."""

    gs: GameState
    player_faction_id: int
    opponent_faction_id: int


class SceneService:

    @staticmethod
    def load_scene(path: str) -> SceneContext:
        component_types: list[type[Any]] = []
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                component_types.append(cls)

        component_types.append(TerrainService.TypeTag)
        component_types.append(CombatUnitService.PlayerFactionTag)
        component_types.append(CombatUnitService.OpponentFactionTag)

        with open(path, "r") as f:
            gs = GameState.load(f.read(), component_types)

        player_faction: int | None = None
        for id, _ in gs.query(CombatUnitService.PlayerFactionTag):
            player_faction = id
        if player_faction == None:
            raise Exception("Player faction not found in save file")

        opponent_faction: int | None = None
        for id, _ in gs.query(CombatUnitService.OpponentFactionTag):
            opponent_faction = id
        if opponent_faction == None:
            raise Exception("Opponent faction not found in save file")

        return SceneContext(
            gs=gs,
            player_faction_id=player_faction,
            opponent_faction_id=opponent_faction,
        )

    @staticmethod
    def save_scene(path: str, gs: GameState) -> None:
        with open(path, "w") as f:
            f.write(gs.save())
