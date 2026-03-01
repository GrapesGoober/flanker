from dataclasses import dataclass
from typing import Literal

from flanker_core.models.components import Vec2
from flanker_core.models.components import InitiativeState



@dataclass
class AiConfigComponent:
    

    @dataclass
    class WaypointsConfig:
        type: Literal["AiWaypointConfig"]
        waypoint_coordinates: list[Vec2]
        path_tolerance: float


    @dataclass
    class RandomHeuristicConfig:  # No config for this one
        type: Literal["AiRandomHeuristicConfig"]
        ...


    @dataclass
    class UnabstractedConfig:  # No config for this one
        type: Literal["AiUnabstractedConfig"]
        ...


    AiConfigTypes = WaypointsConfig | RandomHeuristicConfig | UnabstractedConfig
    faction: InitiativeState.Faction
    config: AiConfigTypes
