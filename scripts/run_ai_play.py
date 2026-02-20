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
    gs = load_game(path="./scenes/demo-simple-stochastic-waypoints.json")
    print("Creating BLUE agent...")
    blue_agent = AiConfigManager.get_agent(gs, InitiativeState.Faction.BLUE)
    print("Creating RED agent...")
    red_agent = AiConfigManager.get_agent(gs, InitiativeState.Faction.RED)

    while ObjectiveSystem.get_winning_faction(gs) == None:
        blue_action_results = blue_agent.play_initiative()
        if blue_action_results:
            print(f"BLUE made actions {blue_action_results}")

        red_action_results = red_agent.play_initiative()
        if red_action_results:
            print(f"RED made actions {red_action_results}")

        if not red_action_results and not blue_action_results:
            print(f"No Valid Actions; Draw")
            break

    print(f"Winner is {ObjectiveSystem.get_winning_faction(gs)}")
