from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_ai.actions import FireActionResult, MoveActionResult
from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_ai.states.waypoints_actions import WaypointMoveAction
from flanker_ai.states.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    MoveControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeState
from flanker_core.systems.register_systems import register_systems


@dataclass
class Fixture:
    gs: GameState
    blue_agent: AiAgent
    friendly_1: UUID
    friendly_2: UUID
    enemy_1: UUID
    enemy_2: UUID


@pytest.fixture
def fixture() -> Fixture:

    gs = GameState()
    register_systems(gs)
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
    )
    friendly_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(1, 12), degrees=-90),
        FireControls(override=FireOutcomes.PIN),
    )
    enemy_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, -15), degrees=70),
    )
    enemy_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.RED),
        FireControls(override=FireOutcomes.PIN),
        Transform(position=Vec2(0, -18), degrees=100),
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
                Vec2(-5, -5),
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
                Vec2(-20, -20),
            ],
            flag=TerrainFeature.Flag.BOUNDARY | TerrainFeature.Flag.OPAQUE,
        ),
    )

    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.BLUE,
            state_config=AiConfigComponent.WaypointsStateConfig(
                type="WaypointsStateConfig",
                waypoint_coordinates=[
                    Vec2(0, 0),  # 0
                    Vec2(10, 1),  # 1
                    Vec2(-10, 1),  # 2
                    Vec2(-10, 10),  # 3
                    Vec2(10, 10),  # 4
                ],
                path_tolerance=3,
            ),
            policy_config=AiConfigComponent.MinimaxPolicyConfig(
                type="MinimaxPolicyConfig"
            ),
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
    )


def test_stall(fixture: Fixture) -> None:
    conf = AiAgent.get_state_config(fixture.gs, InitiativeState.Faction.BLUE)
    assert conf.type == "WaypointsStateConfig"
    rs = WaypointsState(conf.waypoint_coordinates, conf.path_tolerance)
    rs.initialize_state(fixture.gs)
    rs.update_state(fixture.gs)
    for _ in range(5):
        action = WaypointMoveAction(
            unit_id=fixture.friendly_1,
            move_to_waypoint_id=5,
        )
        rs = rs.get_deterministic_branch(action)
    assert rs.get_winner() == None, "BLUE must not stall yet."

    action = WaypointMoveAction(
        unit_id=fixture.friendly_1,
        move_to_waypoint_id=5,
    )
    rs = rs.get_deterministic_branch(action)
    assert (
        rs.get_winner() == InitiativeState.Faction.RED
    ), "BLUE must be considered stall."


def test_waypoints_pathing(fixture: Fixture) -> None:
    conf = AiAgent.get_state_config(fixture.gs, InitiativeState.Faction.BLUE)
    assert conf.type == "WaypointsStateConfig"
    rs = WaypointsState(conf.waypoint_coordinates, conf.path_tolerance)
    rs.initialize_state(fixture.gs)
    rs.update_state(fixture.gs)
    assert rs.waypoints[5].movable_paths[3] == [5, 3]
    assert rs.waypoints[5].movable_paths[2] == [5, 2]
    assert rs.waypoints[5].movable_paths[7] == [5, 6, 0, 7]
    assert rs.waypoints[5].movable_paths[8] == [5, 6, 0, 7, 8]
    assert rs.waypoints[3].movable_paths[7] == [3, 7]
    assert rs.waypoints[3].movable_paths[8] == [3, 7, 8]
    assert rs.waypoints[3].movable_paths[4] == [3, 5, 6, 4]
    assert rs.waypoints[2].movable_paths[1] == [2, 0, 1]


def test_waypoints_visibility(fixture: Fixture) -> None:
    conf = AiAgent.get_state_config(fixture.gs, InitiativeState.Faction.BLUE)
    assert conf.type == "WaypointsStateConfig"
    rs = WaypointsState(conf.waypoint_coordinates, conf.path_tolerance)
    rs.initialize_state(fixture.gs)
    rs.update_state(fixture.gs)
    assert set(rs.waypoints[5].visible_nodes) == {0, 1, 2, 3, 4, 5, 6}
    assert set(rs.waypoints[7].visible_nodes) == {0, 1, 2, 7, 8}


def test_optimal_waypoint(fixture: Fixture) -> None:
    actions = fixture.blue_agent.play_initiative()
    assert actions != [], "The minimax must find optimal action sequence."
    assert isinstance(
        actions[0], MoveActionResult
    ), "AI must start with Move Action to peeking"
    assert isinstance(
        actions[1], MoveActionResult
    ), "AI must start with Move Action to peeking"
    assert actions[0].action.to == Vec2(
        -10, 10
    ), "AI must start with Move Action to peeking"
    assert actions[1].action.to == Vec2(
        -10, 1
    ), "AI must start with Move Action to peeking"
    assert isinstance(actions[2], FireActionResult), "AI must perform Fire Action"
