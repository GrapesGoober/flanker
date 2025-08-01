from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from backend.combat_unit_controller import CombatUnitController
from backend.terrain_controller import TerrainController
from core import components
from core.gamestate import GameState

component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)

component_types.append(TerrainController.TypeTag)
component_types.append(CombatUnitController.PlayerFactionTag)
component_types.append(CombatUnitController.OpponentFactionTag)

with open("./scenes/demo.json", "r") as f:
    data = f.read()

gs = GameState.load(data, component_types)

data = gs.save()
with open("./scenes/demo.json", "w") as f:
    f.write(data)
