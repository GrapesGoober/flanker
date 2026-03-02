from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, InitiativeState, Transform
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.models.vec2 import Vec2

from flanker_ai.unabstracted.random_heuristic_agent import RandomHeuristicAgent
from flanker_ai.unabstracted.models import OrientationActionResult


def test_agent_performs_orientation_first() -> None:
    """Ensure the random heuristic agent will orient towards a nearby enemy before
    taking other actions when its facing is off by a large margin.
    """

    gs = GameState()
    # add initiative state and units
    gs.add_entity(InitiativeState())
    from flanker_core.models.components import FireControls

    blue_id = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, 0), degrees=180),  # facing away from enemy
        FireControls(),
    )
    red_id = gs.add_entity(
        CombatUnit(faction=InitiativeState.Faction.RED),
        Transform(position=Vec2(10, 0)),
        FireControls(),
    )

    InitiativeSystem.set_initiative(gs, InitiativeState.Faction.BLUE)
    agent = RandomHeuristicAgent(InitiativeState.Faction.BLUE, gs)
    results = agent.play_initiative()

    assert results, "Agent should take at least one action"
    # orientation should appear as one of the actions returned
    assert any(isinstance(res, OrientationActionResult) for res in results), (
        "Agent did not return an orientation action when expected"
    )
