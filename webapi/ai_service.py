from flanker_ai.ai_agent import AiAgent, AiWaypointConfig
from flanker_ai.models import (
    ActionResult,
    AssaultActionResult,
    FireActionResult,
    MoveActionResult,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState, TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AiWaypointConfigGridRequest,
    AiWaypointConfigRequest,
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
)


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""

        agent = AiAgent.get_agent(gs, InitiativeState.Faction.RED)

        results = agent.play_initiative()

        AiService._log_ai_action_results(gs, results)

    @staticmethod
    def play_trial(gs: GameState) -> None:
        """Runs a trial where AI plays against each other."""
        blue_agent = AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
        red_agent = AiAgent.get_agent(gs, InitiativeState.Faction.RED)
        while (winner := ObjectiveSystem.get_winning_faction(gs)) == None:
            blue_action_results = blue_agent.play_initiative()
            if blue_action_results:
                AiService._log_ai_action_results(gs, blue_action_results)

            red_action_results = red_agent.play_initiative()
            if red_action_results:
                AiService._log_ai_action_results(gs, red_action_results)

            if not red_action_results and not blue_action_results:
                print(f"No Valid Actions; Draw")
                break
        if winner == None:
            print(f"No winner; draw")
        else:
            print(f"Winner is {winner}")

    @staticmethod
    def set_ai_waypoints_config(
        gs: GameState,
        request: AiWaypointConfigRequest,
    ) -> None:
        config = AiAgent.get_ai_config(gs, request.faction)
        if isinstance(config, AiWaypointConfig):
            config.waypoint_coordinates = request.points

    @staticmethod
    def set_ai_waypoints_config_to_grid(
        gs: GameState,
        request: AiWaypointConfigGridRequest,
    ) -> None:
        config = AiAgent.get_ai_config(gs, request.faction)
        if isinstance(config, AiWaypointConfig):
            config.path_tolerance = request.spacing
            config.waypoint_coordinates = AiService.get_grid_coordinates(
                gs, spacing=request.spacing, offset=request.spacing / 2
            )

    @staticmethod
    def get_grid_coordinates(
        gs: GameState,
        spacing: float,
        offset: float,
    ) -> list[Vec2]:

        # Build an array of grids within the boundary
        mask = TerrainFeature.Flag.BOUNDARY
        boundary_vertices: list[Vec2] | None = None
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])

        assert boundary_vertices, "Can't abstract; boundary terrain missing!"

        # Boundary terrrain might not be a box
        min_x = min(v.x for v in boundary_vertices) + offset
        max_x = max(v.x for v in boundary_vertices)
        min_y = min(v.y for v in boundary_vertices) + offset
        max_y = max(v.y for v in boundary_vertices)

        # Generates waypoints at specified spacing
        points: list[Vec2] = []
        y = min_y
        while y <= max_y:
            x = min_x
            while x <= max_x:
                p = Vec2(x, y)

                # Keep only points inside polygon
                if IntersectGetter.is_inside(p, boundary_vertices):
                    points.append(p)

                x += spacing
            y += spacing
        return points

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
