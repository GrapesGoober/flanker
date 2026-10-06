from dataclasses import dataclass
from uuid import UUID

from flanker_ai.config_models import TranspositionScheme
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
from flanker_core.systems.action_system import ActionSystem


@dataclass(frozen=True)
class CombatUnitKey:

    type PositionalFeature = tuple[int, int]
    type RotationalFeature = int
    type Feature = PositionalFeature | RotationalFeature

    id: UUID
    features: tuple[Feature, ...]
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


class AiCacheKeyService:
    """Utility for creating a cache key of a game state."""

    @staticmethod
    def get_key(
        gs: GameState,
        transposition_schemes: list[TranspositionScheme.ALL],
    ) -> CacheKey:
        """
        Get a hashable cache key given this game state. This key is
        a unique representation of the game state.
        """

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

        combat_units_keys = AiCacheKeyService.get_combat_unit_key(
            gs, transposition_schemes
        )

        return CacheKey(
            initiative=ActionSystem.get_initiative(gs),
            combat_units=tuple(combat_units_keys),
            eliminations=tuple(eliminations),
            stalls=tuple(stalls),
        )

    @staticmethod
    def get_combat_unit_key(
        gs: GameState,
        transposition_schemes: list[TranspositionScheme.ALL],
    ) -> list[CombatUnitKey]:

        combat_units: list[CombatUnitKey] = []

        for id, transform, unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            features: list[CombatUnitKey.Feature] = []
            for transposition_scheme in transposition_schemes:
                match transposition_scheme:
                    case TranspositionScheme.NearestPositionInteger():
                        feature = (
                            int(round(transform.position.x)),
                            int(round(transform.position.y)),
                        )
                    case TranspositionScheme.NearestRotationInteger():
                        feature = int(round(transform.degrees))
                features.append(feature)

            combat_units.append(
                CombatUnitKey(
                    id=id,
                    features=tuple(features),
                    faction=unit.faction,
                    firing_at=fire_controls.firing_at,
                )
            )
        return combat_units
