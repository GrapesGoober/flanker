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
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
)


@dataclass
class _AiPlayer:
    faction: InitiativeState.Faction
    player: WaypointsMinimaxPlayer


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def get_player(
        gs: GameState, faction: InitiativeState.Faction
    ) -> WaypointsMinimaxPlayer:

        player: WaypointsMinimaxPlayer | None = None
        for _, player_component in gs.query(_AiPlayer):
            if player_component.faction != faction:
                continue
            player = player_component.player
        if player is None:
            player = WaypointsMinimaxPlayer(
                gs=gs,
                faction=faction,
                search_depth=4,
                grid_spacing=20,
                grid_offset=10,
            )
            gs.add_entity(_AiPlayer(faction=faction, player=player))
        return player

    @staticmethod
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""

        player = AiService.get_player(gs, InitiativeState.Faction.RED)

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

    # @staticmethod
    # def upsert_waypoints(gs: GameState, points: list[Vec2]) -> None:
    #     if results := gs.query(_AiPlayer):
    #         _, player_component = results[0]
    #         player = player_component.player
    #     else:
    #         player = WaypointsMinimaxPlayer(
    #             gs=gs,
    #             faction=InitiativeState.Faction.RED,
    #             search_depth=4,
    #             grid_spacing=20,
    #             grid_offset=10,
    #         )
    #         gs.add_entity(_AiPlayer(player, points=[]))
