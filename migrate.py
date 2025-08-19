from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from backend.terrain_service import TerrainTypeTag
from core import components
from core.gamestate import GameState
from core.serializer import Serializer
from core.utils.vec2 import Vec2


component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)
component_types.append(TerrainTypeTag)

path = "./scenes/demo.json"

with open(path, "r") as f:
    entities, _ = Serializer.deserialize(f.read(), component_types)

gs = GameState()
for i in list(entities.values())[:11]:
    gs.add_entity(*i.values())

gs.add_entity(
    components.Transform(position=Vec2(200, 212)),
    components.CombatUnit(faction=components.InitiativeState.Faction.RED),
    components.MoveControls(),
    components.FireControls(),
    components.AssaultControls(),
)

gs.add_entity(
    components.Transform(position=Vec2(210, 212)),
    components.CombatUnit(faction=components.InitiativeState.Faction.RED),
    components.MoveControls(),
    components.FireControls(),
    components.AssaultControls(),
)

for i in list(entities.values())[11:]:
    gs.add_entity(*i.values())

with open(path, "w") as f:
    f.write(gs.save())
