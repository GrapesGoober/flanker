from dataclasses import dataclass
from uuid import UUID

from flanker_ai.config_models import TranspositionScheme
from flanker_ai.search_states.common.ai_aspect_signature_service import (
    AiAspectSignatureService,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    StallLoseCondition,
    Transform,
)
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.los_system import LosSystem


@dataclass(frozen=True)
class CombatUnitSignature:
    faction: InitiativeState.Faction
    status: CombatUnit.Status


@dataclass(frozen=True)
class CombatUnitKey:

    type RoundedPosition = tuple[int, int]
    type RoundedRotation = int
    type LosSignature = tuple[bool, ...]
    type AspectSignature = tuple[UUID | CombatUnitSignature, ...]
    type Feature = RoundedPosition | RoundedRotation | LosSignature | AspectSignature

    features: tuple[Feature, ...]
    unit_signature: CombatUnitSignature


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
    """Utility for creating a Zobrist transposition key of a game state."""

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

        for unit_id, transform, unit in gs.query(Transform, CombatUnit):
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
                            unit_id=unit_id,
                            with_fov=transposition_scheme.with_fov,
                        )
                    case TranspositionScheme.AspectSignatures():
                        feature = (
                            AiTranspositionKeyService._get_aspect_signature_of_unit(
                                gs=gs, unit_id=unit_id
                            )
                        )

                features.append(feature)

            combat_units.append(
                CombatUnitKey(
                    features=tuple(features),
                    unit_signature=CombatUnitSignature(
                        faction=unit.faction,
                        status=unit.status,
                    ),
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

    @staticmethod
    def _get_aspect_signature_of_unit(
        gs: GameState,
        unit_id: UUID,
    ) -> CombatUnitKey.AspectSignature:

        # TODO: build aspects with other units too, not just against terrains.
        unit_transform = gs.get_component(unit_id, Transform)
        obstacle_angles = AiAspectSignatureService.get_aspects_angles(
            gs=gs,
            position=unit_transform.position,
        )
        obstacle_angles.sort(key=lambda obstacle: obstacle[0])
        obstacle_ids = [terrain_id for terrain_id, _ in obstacle_angles]
        return tuple(obstacle_ids)
