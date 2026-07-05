from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_ai.actions import FireActionResult, MoveActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import (
    PointsConfig,
    SearchPolicyConfig,
    WaypointsStateConfig,
)
from flanker_ai.states.waypoints.waypoints_graph_system import WaypointsGraphSystem
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    MoveControls,
    StallLoseCondition,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeState


@dataclass
class Fixture:
    gs: GameState
    blue_agent: AiAgent
    friendly_1: UUID
    friendly_2: UUID
    enemy_1: UUID
    enemy_2: UUID
    waypoint_coordinates: list[Vec2]


@pytest.fixture
def fixture() -> Fixture:

    gs = GameState()
    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
    )
    friendly_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(-1, 12), degrees=-90),
        FireControls(override=FireOutcomes.PIN),
        AssaultControls(),
    )
    friendly_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(1, 12), degrees=-90),
        FireControls(override=FireOutcomes.PIN),
        AssaultControls(),
    )
    enemy_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, -15), degrees=70),
        AssaultControls(),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, -18), degrees=100),
        AssaultControls(),
    )

    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-5, -5),
                Vec2(5, -5),
                Vec2(5, 5),
                Vec2(-5, 5),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )
    # 40x40 boundary
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(-20, -20),
                Vec2(20, -20),
                Vec2(20, 20),
                Vec2(-20, 20),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    waypoint_coordinates = [
        Vec2(0, 0),  # 0
        Vec2(10, 1),  # 1
        Vec2(-10, 1),  # 2
        Vec2(-10, 10),  # 3
        Vec2(10, 10),  # 4
    ]

    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.BLUE,
            config=SearchPolicyConfig(
                policy_type="Minimax",
                state=WaypointsStateConfig(
                    type="WaypointsStateConfig",
                    waypoints=PointsConfig(
                        initial_points=PointsConfig.HandDrawnConfig(
                            type="HandDrawnConfig",
                            points=waypoint_coordinates,
                        ),
                        use_combat_unit_positions=False,
                        expansions=[],
                    ),
                    path_tolerance=3,
                ),
            ),
        )
    )
    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        )
    )
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            stall_count=0,
            stall_limit=5,
        )
    )
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            stall_count=0,
            stall_limit=5,
        )
    )

    blue_agent = AiAgent.get_agent(gs, faction=InitiativeState.Faction.BLUE)

    return Fixture(
        gs=gs,
        blue_agent=blue_agent,
        friendly_1=friendly_1,
        friendly_2=friendly_2,
        enemy_1=enemy_1,
        enemy_2=enemy_2,
        waypoint_coordinates=waypoint_coordinates,
    )


def test_waypoints_pathing(fixture: Fixture) -> None:
    agent = fixture.blue_agent
    rs = agent.rs
    assert isinstance(
        rs, WaypointsState
    ), "Configured agent's state representation must be waypoints state."
    rs.update_state(fixture.gs)
    waypoints_system = rs.gs.get(WaypointsGraphSystem)
    waypoints = waypoints_system.get_waypoints(rs.gs)
    assert waypoints[5].movable_paths[3] == [5, 3]
    assert waypoints[5].movable_paths[2] == [5, 2]
    assert waypoints[5].movable_paths[7] == [5, 6, 0, 7]
    assert waypoints[5].movable_paths[8] == [5, 6, 0, 7, 8]
    assert waypoints[3].movable_paths[7] == [3, 7]
    assert waypoints[3].movable_paths[8] == [3, 7, 8]
    assert waypoints[3].movable_paths[4] == [3, 5, 6, 4]
    assert waypoints[2].movable_paths[1] == [2, 0, 1]


def test_waypoints_visibility(fixture: Fixture) -> None:
    agent = fixture.blue_agent
    rs = agent.rs
    assert isinstance(
        rs, WaypointsState
    ), "Configured agent's state representation must be waypoints state."
    rs.update_state(fixture.gs)
    waypoints_system = rs.gs.get(WaypointsGraphSystem)
    waypoints = waypoints_system.get_waypoints(rs.gs)
    assert set(waypoints[5].visible_nodes) == {0, 1, 2, 3, 4, 5, 6}
    assert set(waypoints[7].visible_nodes) == {0, 1, 2, 7, 8}


def test_optimal_waypoints(fixture: Fixture) -> None:
    action_results = fixture.blue_agent.play_initiative()
    assert action_results != [], "The minimax must find optimal action sequence."

    staging_units: list[UUID] = []
    for result, _ in action_results:
        if not isinstance(result, MoveActionResult):
            continue
        if result.action.to == Vec2(-10, 10):
            staging_units.append(result.action.unit_id)
    assert len(staging_units) != 0, "AI must try staging to Vec2(-10, 10)."

    peeking_units: list[UUID] = []
    for result, _ in action_results:
        if not isinstance(result, MoveActionResult):
            continue
        if result.action.to == Vec2(-10, 1):
            peeking_units.append(result.action.unit_id)
    assert len(peeking_units) != 0, "AI must try peeking to Vec2(-10, 1)."

    assert set(peeking_units).issubset(
        set(staging_units)
    ), "Peeking units must be staged first."

    last_action_result, _ = action_results[-1]
    assert isinstance(
        last_action_result, FireActionResult
    ), "AI must fire at the enemy once."
