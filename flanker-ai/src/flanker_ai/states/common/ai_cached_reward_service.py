from dataclasses import dataclass
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    StallLoseCondition,
    Transform,
)
from flanker_core.models.outcomes import FireEffect
from flanker_core.systems.initiative_system import InitiativeSystem


@dataclass(frozen=True)
class CombatUnitKey:
    id: UUID
    position: tuple[int, int]
    degrees: int
    faction: InitiativeState.Faction
    firing_at: tuple[UUID, FireEffect] | None = None


@dataclass(frozen=True)
class EliminationKey:
    target_faction: InitiativeState.Faction
    winning_faction: InitiativeState.Faction
    units_to_eliminate: int
    units_eliminated_counter: int


@dataclass(frozen=True)
class StallsKey:
    counting_faction: InitiativeState.Faction
    winning_faction: InitiativeState.Faction
    stall_count: int
    stall_limit: int


@dataclass(frozen=True)
class CacheKey:
    initiative: InitiativeState.Faction
    combat_units: tuple[CombatUnitKey, ...]
    eliminations: tuple[EliminationKey, ...]
    stalls: tuple[StallsKey, ...]


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
        for id, transform, unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            combat_units.append(
                CombatUnitKey(
                    id=id,
                    position=(
                        int(round(transform.position.x)),
                        int(round(transform.position.y)),
                    ),
                    degrees=int(round(transform.degrees)),
                    faction=unit.faction,
                    firing_at=fire_controls.firing_at,
                )
            )

        eliminations: list[EliminationKey] = []
        for _, elimination in gs.query(EliminationWinCondition):
            eliminations.append(
                EliminationKey(
                    target_faction=elimination.target_faction,
                    winning_faction=elimination.winning_faction,
                    units_to_eliminate=elimination.units_to_eliminate,
                    units_eliminated_counter=elimination.units_eliminated_counter,
                )
            )

        stalls: list[StallsKey] = []
        for _, stall in gs.query(StallLoseCondition):
            stalls.append(
                StallsKey(
                    counting_faction=stall.counting_faction,
                    winning_faction=stall.winning_faction,
                    stall_count=stall.stall_count,
                    stall_limit=stall.stall_limit,
                )
            )

        return CacheKey(
            initiative=InitiativeSystem.get_initiative(gs),
            combat_units=tuple(combat_units),
            eliminations=tuple(eliminations),
            stalls=tuple(stalls),
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
