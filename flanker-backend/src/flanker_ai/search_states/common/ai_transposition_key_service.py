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
from flanker_core.systems.los_system import LosSystem


@dataclass(frozen=True)
class CombatUnitKey:

    type RoundedPosition = tuple[int, int]
    type RoundedRotation = int
    type LosSignature = tuple[bool, ...]
    type Feature = RoundedPosition | RoundedRotation | LosSignature

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


class AiTranspositionKeyService:
    """Utility for creating a transposition key of a game state."""

    @staticmethod
    def get_key(
        gs: GameState,
        transposition_schemes: list[TranspositionScheme.ALL],
    ) -> CacheKey:
        """
        Get a hashable transposition key object of a game state.
        This key is a compressed value-based descriptor of a state.
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

        combat_units_keys = AiTranspositionKeyService.get_combat_unit_key(
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
                    case TranspositionScheme.RoundedPosition():
                        to_nearest = transposition_scheme.to_nearest
                        feature = (
                            int(round(transform.position.x / to_nearest)),
                            int(round(transform.position.y / to_nearest)),
                        )
                    case TranspositionScheme.RoundedRotation():
                        to_nearest = transposition_scheme.to_nearest
                        feature = int(round(transform.degrees / to_nearest))
                    case TranspositionScheme.LosSignatures():
                        feature = AiTranspositionKeyService._get_los_signature_of_unit(
                            gs=gs,
                            unit_id=id,
                            with_fov=transposition_scheme.with_fov,
                        )

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

    @staticmethod
    def _get_los_signature_of_unit(
        gs: GameState,
        unit_id: UUID,
        with_fov: bool,
    ) -> tuple[bool, ...]:
        unit_position = gs.get_component(unit_id, Transform).position
        los_signatures: list[bool] = []
        for other_id, _, other_transform, other_fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):
            has_los = LosSystem.has_los(
                gs,
                other_transform.position,
                unit_position,
            )

            if with_fov == True and other_fire_controls.fov_degrees != None:
                in_fov = LosSystem.in_fov(gs, other_id, unit_position)
                has_los = has_los and in_fov

            los_signatures.append(has_los)

        return tuple(los_signatures)
