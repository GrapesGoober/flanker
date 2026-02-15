#!/usr/bin/env python3
"""
Script to run the random heuristic AI player in the experiment.
"""

import json
from flanker_core.gamestate import GameState
from flanker_core.serializer import Serializer
from flanker_core.models.components import (
    InitiativeState,
    EliminationObjective,
    Transform,
    CombatUnit,
    TerrainFeature,
)
from webapi.ai_service import AiService


def main():
    # Load a scene
    with open("scenes/demo.json", "r") as f:
        scene_data = json.load(f)

    # Deserialize
    component_types = [InitiativeState, EliminationObjective, Transform, CombatUnit, TerrainFeature]
    entities, id_counter = Serializer.deserialize(json.dumps(scene_data), component_types)
    gs = GameState.load(entities, id_counter)

    # Run the random heuristic AI for REDFOR
    AiService.play_random_heuristic(gs)

    # Print final state or something
    print("Experiment completed.")


if __name__ == "__main__":
    main()