from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.ai_config_manager import AiConfigComponent, AiConfigManager
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.objective_system import ObjectiveSystem


def initialize_game_state(path: str) -> GameState:
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
        gs = GameState.load(entities, id_counter)

    print("Creating BLUE agent...")
    AiConfigManager.get_agent(gs, InitiativeState.Faction.BLUE)
    print("Creating RED agent...")
    AiConfigManager.get_agent(gs, InitiativeState.Faction.RED)
    return gs


def run_test(gs: GameState, n: int = 1):
    for i in range(n):
        print(f"Running Trial {i=}...")
        new_gs = deepcopy(gs)
        blue_agent = AiConfigManager.get_agent(new_gs, InitiativeState.Faction.BLUE)
        red_agent = AiConfigManager.get_agent(new_gs, InitiativeState.Faction.RED)
        while ObjectiveSystem.get_winning_faction(new_gs) == None:
            blue_action_results = blue_agent.play_initiative()
            if blue_action_results:
                print(f"BLUE made actions {blue_action_results}")

            red_action_results = red_agent.play_initiative()
            if red_action_results:
                print(f"RED made actions {red_action_results}")

            if not red_action_results and not blue_action_results:
                print(f"No Valid Actions; Draw")
                break
        print(f"Winner is {ObjectiveSystem.get_winning_faction(new_gs)}")


if __name__ == "__main__":
    SCENE_FILE = "./scenes/experiment-w1-w1-2v2.json"
    gs = initialize_game_state(path=SCENE_FILE)
    run_test(gs, n=2)
