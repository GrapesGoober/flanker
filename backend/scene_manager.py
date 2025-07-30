from dataclasses import dataclass, is_dataclass
from inspect import isclass
from typing import Any
from backend import CombatUnitController
from backend.terrain_controller import TerrainController
from core.gamestate import GameState
from core import components


@dataclass
class SceneContext:
    """Holds the game state and faction IDs for a scene."""

    gs: GameState
    player_faction_id: int
    opponent_faction_id: int


class SceneManager:

    @staticmethod
    def load_scene(path: str) -> SceneContext:
        manifest: list[type[Any]] = []
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                manifest.append(cls)

        manifest.append(TerrainController.TypeTag)
        manifest.append(CombatUnitController.PlayerFactionTag)
        manifest.append(CombatUnitController.OpponentFactionTag)

        with open(path, "r") as f:
            gs = GameState.load(f.read(), manifest)

        player_faction: int | None = None
        for id, _ in gs.query(CombatUnitController.PlayerFactionTag):
            player_faction = id
        if player_faction == None:
            raise Exception("Player faction not found in save file")

        opponent_faction: int | None = None
        for id, _ in gs.query(CombatUnitController.OpponentFactionTag):
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
