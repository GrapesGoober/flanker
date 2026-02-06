from dataclasses import dataclass

from flanker_ai.unabstracted.models import (
    ActionResult,
    AssaultActionResult,
    FireActionResult,
    MoveActionResult,
)
from flanker_ai.unabstracted.tree_search_player import TreeSearchPlayer
from flanker_ai.waypoints.models import WaypointAction
from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AiWaypointConfigRequest,
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
)


# TODO: this AI config things could be moved to flanker_ai package
# keep the configuration logic shared and standardized.
@dataclass
class _AiConfig:
    faction: InitiativeState.Faction
    points: list[Vec2]
    player: WaypointsMinimaxPlayer | None = None


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def _get_ai_config(gs: GameState, faction: InitiativeState.Faction) -> _AiConfig:
        # Get the singleton config. If not exist, create a new empty one
        config: _AiConfig | None = None
        for _, c in gs.query(_AiConfig):
            if c.faction != faction:
                continue
            config = c
            break
        if config is None:
            gs.add_entity(config := _AiConfig(faction=faction, points=[]))
        return config

    @staticmethod
    def _get_player(
        gs: GameState, faction: InitiativeState.Faction
    ) -> WaypointsMinimaxPlayer:

        config = AiService._get_ai_config(gs, faction)

        # Add a new player if not exist
        if config.player is None:
            if config.points == []:
                config.points = WaypointScheme.get_grid_coordinates(
                    gs, spacing=20, offset=10
                )
            config.player = WaypointsMinimaxPlayer(
                gs=gs,
                faction=faction,
                search_depth=4,
                waypoint_coordinates=config.points,
                path_tolerance=10,
            )

        return config.player

    @staticmethod
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""

        player = AiService._get_player(gs, InitiativeState.Faction.RED)

        def print_actions_sequence(actions: list[WaypointAction]) -> None:
            print(f"Action sequences {actions}")

        results = player.play_initiative(
            sequence_callback=print_actions_sequence,
        )

        AiService._log_ai_action_results(gs, results)

    @staticmethod
    def _log_ai_action_results(
        gs: GameState,
        results: list[ActionResult],
    ) -> None:
        for result in results:
            match result:
                case MoveActionResult():
                    log = MoveActionLog(
                        body=MoveActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcome=result.reactive_fire_outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case FireActionResult():
                    log = FireActionLog(
                        body=FireActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case AssaultActionResult():
                    log = AssaultActionLog(
                        body=AssaultActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case _:
                    raise ValueError(f"Unknown type {result=}")

            LoggingService.log(gs, log)

    @staticmethod
    def play_minimax(gs: GameState, depth: int) -> None:
        """
        (prototype) Runs an unabstracted minimax search and logs
        sequential results for a BLUE faction.
        """

        _, results = TreeSearchPlayer.play_minimax(gs, depth)
        LoggingService.clear_logs(gs)
        AiService._log_ai_action_results(gs, results)

    @staticmethod
    def update_ai_config(
        gs: GameState,
        request: AiWaypointConfigRequest,
    ) -> None:
        config = AiService._get_ai_config(gs, request.faction)
        config.points = request.points
