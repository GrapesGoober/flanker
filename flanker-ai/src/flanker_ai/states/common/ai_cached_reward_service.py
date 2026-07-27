from dataclasses import dataclass
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import FireEffect
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem


@dataclass(frozen=True)
class CombatUnitKey:
    position: Vec2
    degrees: float
    faction: InitiativeState.Faction
    firing_at: tuple[UUID, FireEffect] | None = None


@dataclass(frozen=True)
class CacheKey:
    initiative: InitiativeState.Faction
    combat_units: tuple[CombatUnitKey, ...]


@dataclass
class TranspositionTable:
    table: dict[CacheKey, float]


class AiCachedRewardService:
    """Utility for a cached reward table."""

    @staticmethod
    def get_key(
        gs: GameState,
    ) -> CacheKey:

        combat_units: list[CombatUnitKey] = []
        for _, transform, unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            combat_units.append(
                CombatUnitKey(
                    position=(
                        int(round(transform.position.x)),
                        int(round(transform.position.y)),
                    ),
                    degrees=int(round(transform.degrees)),
                    faction=unit.faction,
                    firing_at=fire_controls.firing_at,
                )
            )

        return CacheKey(
            initiative=InitiativeSystem.get_initiative(gs),
            combat_units=tuple(combat_units),
        )

    @staticmethod
    def get_transposition_table(
        gs: GameState,
    ) -> dict[CacheKey, float]:
        if entities := gs.query(TranspositionTable):
            _, component = entities[0]
        else:
            gs.add_entity(
                component := TranspositionTable(
                    cache_hits=0,
                    table={},
                )
            )
        return component.table

    @staticmethod
    def get_reward(
        gs: GameState,
    ) -> float | None:
        key = AiCachedRewardService.get_key(gs)
        table = AiCachedRewardService.get_transposition_table(gs)
        return table.get(key, None)

    @staticmethod
    def set_reward(
        gs: GameState,
        value: float,
    ) -> None:
        key = AiCachedRewardService.get_key(gs)
        table = AiCachedRewardService.get_transposition_table(gs)
        table[key] = value
