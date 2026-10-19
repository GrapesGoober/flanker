from typing import Annotated, Literal, Union

from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from webapi.models.action_models import ActionRequest
from webapi.models.state_models import GameViewState


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class GameStateInspection(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the game state."""

    class LosPolygon(BaseModel, CamelCaseConfig):
        faction: InitiativeState.Faction
        los_polygon: list[Vec2]
        fov_polygon: list[Vec2]

    view_state: GameViewState
    los_polygons: list[LosPolygon]
    move_candidates: list[Vec2]
    units_aspects: list[tuple[Vec2, list[float]]]


class MctsTreeInspectionEdge(BaseModel, CamelCaseConfig):
    """An MCTS tree edge."""

    action: ActionRequest
    node: "MctsTreeInspectionNode"


class MctsTreeInspectionNode(BaseModel, CamelCaseConfig):
    """An MCTS tree node."""

    view_state: GameViewState
    children: list[MctsTreeInspectionEdge]
    total_visits: int
    total_value: float


class MctsTreeInspection(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the MCTS game tree."""

    type: Literal["MctsTreeInspection"]
    best_action: ActionRequest
    tree_root: MctsTreeInspectionNode


class MinimaxTreeInspectionNode(BaseModel, CamelCaseConfig):
    "A Minimax tree node."

    view_state: GameViewState
    children: list["MinimaxTreeInspectionEdge"]


class MinimaxTreeInspectionEdge(BaseModel, CamelCaseConfig):
    "A Minimax tree edge."

    action: ActionRequest
    node: "MinimaxTreeInspectionNode"
    best_score: float


class MinimaxTreeInspection(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the Minimax game tree."""

    type: Literal["MinimaxTreeInspection"]
    best_action: ActionRequest
    tree_root: MinimaxTreeInspectionNode


class ExpectimaxTreeInspectionOutcome(BaseModel, CamelCaseConfig):
    """A probabilistic outcome of an expectimax action."""

    probability: float
    node: "ExpectimaxTreeInspectionNode"
    score: float


class ExpectimaxTreeInspectionEdge(BaseModel, CamelCaseConfig):
    """An expectimax action and its probabilistic outcomes."""

    action: ActionRequest
    outcomes: list[ExpectimaxTreeInspectionOutcome]
    expected_score: float


class ExpectimaxTreeInspectionNode(BaseModel, CamelCaseConfig):
    """An expectimax tree node."""

    view_state: GameViewState
    children: list[ExpectimaxTreeInspectionEdge]


class ExpectimaxTreeInspection(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the Expectimax game tree."""

    type: Literal["ExpectimaxTreeInspection"]
    best_action: ActionRequest
    tree_root: ExpectimaxTreeInspectionNode


type GameTreeInspection = Annotated[
    Union[
        MinimaxTreeInspection,
        MctsTreeInspection,
        ExpectimaxTreeInspection,
    ],
    Field(discriminator="type"),
]
