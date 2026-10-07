from typing import FrozenSet
from uuid import UUID

from flanker_ai.agents.ai_search_agent import AiSearchAgent
from flanker_ai.config_models import AiConfigComponent, SearchPolicyConfig
from flanker_ai.search_states.common.ai_aspect_boundary_service import (
    AiAspectBoundaryService,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import MoveAction
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.utils.polygon_utils import PolygonUtils
from webapi.models import (
    FireEffectPair,
    GameStateInspection,
    GameViewState,
    GameViewStateResponse,
    SquadModel,
)
from webapi.services.scene_service import SceneService


class GameViewService:

    @staticmethod
    def get_view_state(gs: GameState) -> GameViewState:
        """Get a view version of game state."""
        # Assume player faction is BLUE
        faction = InitiativeState.Faction.BLUE

        # Grab all the squads and build its view models
        squads: list[SquadModel] = []
        fire_effect_pairs: dict[FrozenSet[UUID], FireEffectPair] = {}
        for unit_id, unit, transform, fire_controls in gs.query(
            CombatUnit,
            Transform,
            FireControls,
        ):
            squads.append(
                SquadModel(
                    unit_id=unit_id,
                    position=transform.position,
                    degrees=transform.degrees,
                    status=unit.status,
                    is_friendly=(unit.faction == faction),
                    fov_degrees=fire_controls.fov_degrees,
                    firing_at=fire_controls.firing_at,
                )
            )

            if fire_controls.firing_at != None:
                target_id, fire_effect = fire_controls.firing_at
                fire_effect_key = frozenset((unit_id, target_id))
                if fire_effect_key in fire_effect_pairs:
                    fire_effect_pairs[fire_effect_key].fire_effect_b = fire_effect
                else:
                    target_transform = gs.get_component(target_id, Transform)
                    fire_effect_pairs[fire_effect_key] = FireEffectPair(
                        position_a=transform.position,
                        position_b=target_transform.position,
                        fire_effect_a=fire_effect,
                        fire_effect_b=None,
                    )

        # Grab all the game match data
        has_initiative = ActionSystem.get_initiative(gs) == faction
        winning_faction = ObjectiveSystem.get_winning_faction(gs)
        if winning_faction == faction:
            objective_state = GameViewState.ObjectiveState.COMPLETED
        elif winning_faction == None:
            objective_state = GameViewState.ObjectiveState.INCOMPLETE
        else:
            objective_state = GameViewState.ObjectiveState.FAILED

        return GameViewState(
            objective_state=objective_state,
            has_initiative=has_initiative,
            squads=squads,
            fire_effect_pairs=list(fire_effect_pairs.values()),
        )

    @staticmethod
    def get_view_state_response(gs: GameState) -> GameViewStateResponse:
        return GameViewStateResponse(
            view_state=GameViewService.get_view_state(gs),
            json_state=SceneService.serialize(gs),
        )

    @staticmethod
    def get_inspection(
        gs: GameState,
    ) -> GameStateInspection:
        los_polygons: list[GameStateInspection.LosPolygon] = []
        unit_aspects: list[tuple[Vec2, list[float]]] = []
        for _, unit, transform, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):
            los_polygon = LosSystem.get_los_polygon(
                gs,
                spotter_pos=transform.position,
            )

            if fire_controls.fov_degrees != None:
                fov_polygon = PolygonUtils.clip_by_fov_cone(
                    polyline=los_polygon,
                    center_point=transform.position,
                    heading_degree=transform.degrees,
                    fov_degrees=fire_controls.fov_degrees,
                )
            else:
                fov_polygon = los_polygon

            los_polygons.append(
                GameStateInspection.LosPolygon(
                    faction=unit.faction,
                    los_polygon=los_polygon,
                    fov_polygon=fov_polygon,
                )
            )

            aspect = AiAspectBoundaryService.get_aspects_boundaries(gs, transform)
            unit_aspects.append((transform.position, aspect))

        config: SearchPolicyConfig | None = None
        for _, component in gs.query(AiConfigComponent):
            if component.faction != InitiativeState.Faction.BLUE:
                continue
            if not isinstance(component.config, SearchPolicyConfig):
                continue
            config = component.config

        move_candidates: list[Vec2] = []
        if config != None:
            state = AiSearchAgent.get_state(
                gs=gs,
                config=config,
            )
            actions = [a for a in state.get_actions() if isinstance(a, MoveAction)]
            unit_id = actions[0].unit_id if actions else None
            move_candidates = [a.to for a in actions if a.unit_id == unit_id]

        return GameStateInspection(
            view_state=GameViewService.get_view_state(gs),
            los_polygons=los_polygons,
            move_candidates=move_candidates,
            units_aspects=unit_aspects,
        )
