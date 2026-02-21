from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.ai_config_manager import AiConfigComponent, AiConfigManager
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.objective_system import ObjectiveSystem


def load_game(path: str) -> GameState:
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    with open(path, "r") as f:
        entities, id_counter = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        return GameState.load(entities, id_counter)


if __name__ == "__main__":
    gs = load_game(path="./scenes/experiment-wh.json")
    print("Creating RED agent...")
    red_agent = AiConfigManager.get_agent(gs, InitiativeState.Faction.RED)
    print("Creating BLUE agent...")
    blue_agent = AiConfigManager.get_agent(gs, InitiativeState.Faction.BLUE)

    while ObjectiveSystem.get_winning_faction(gs) == None:
        results = red_agent.play_initiative()
        if results:
            print(f"RED made actions {results}")

        results = blue_agent.play_initiative()
        if results:
            print(f"BLUE made actions {results}")

    print(f"Winner is {ObjectiveSystem.get_winning_faction(gs)}")
