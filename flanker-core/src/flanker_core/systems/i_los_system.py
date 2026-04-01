from abc import ABC, abstractmethod

from flanker_ai.actions import GameState
from flanker_core.models.vec2 import Vec2


class ILosSystem(ABC):

    @staticmethod
    @abstractmethod
    def has_los(gs: GameState, spotter_pos: Vec2, target_pos: Vec2) -> bool:
        """
        Returns `True` if entity `spotter_id` can see position `target_pos`.
        Does not check for FOV.
        """
