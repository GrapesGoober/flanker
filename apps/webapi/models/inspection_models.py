from typing import Annotated, Literal, Union

from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from webapi.models.action_models import ActionModel
from webapi.models.state_models import GameViewState


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class GameStateInspectionModel(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the game state."""

    class LosPolygon(BaseModel, CamelCaseConfig):
        faction: InitiativeState.Faction
        los_polygon: list[Vec2]
        fov_polygon: list[Vec2]

    view_state: GameViewState
    los_polygons: list[LosPolygon]
    move_candidates: list[Vec2]
    units_aspects: list[tuple[Vec2, list[float]]]


class MctsTreeEdgeModel(BaseModel, CamelCaseConfig):
    """An MCTS tree edge."""

    action: ActionModel
    node: "MctsTreeNodeModel"


class MctsTreeNodeModel(BaseModel, CamelCaseConfig):
    """An MCTS tree node."""

    view_state: GameViewState
    children: list[MctsTreeEdgeModel]
    total_visits: int
    total_value: float


class MctsTreeInspectionModel(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the MCTS game tree."""

    type: Literal["MctsTreeInspectionModel"]
    best_action: ActionModel
    tree_root: MctsTreeNodeModel


class MinimaxTreeNodeModel(BaseModel, CamelCaseConfig):
    "A Minimax tree node."

    view_state: GameViewState
    children: list["MinimaxTreeEdgeModel"]


class MinimaxTreeEdgeModel(BaseModel, CamelCaseConfig):
    "A Minimax tree edge."

    action: ActionModel
    node: "MinimaxTreeNodeModel"
    best_score: float


class MinimaxTreeInspectionModel(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the Minimax game tree."""

    type: Literal["MinimaxTreeInspectionModel"]
    best_action: ActionModel
    tree_root: MinimaxTreeNodeModel


class ExpectimaxTreeOutcomeModel(BaseModel, CamelCaseConfig):
    """A probabilistic outcome of an expectimax action."""

    probability: float
    node: "ExpectimaxTreeNodeModel"
    score: float


class ExpectimaxTreeEdgeModel(BaseModel, CamelCaseConfig):
    """An expectimax action and its probabilistic outcomes."""

    action: ActionModel
    outcomes: list[ExpectimaxTreeOutcomeModel]
    expected_score: float


class ExpectimaxTreeNodeModel(BaseModel, CamelCaseConfig):
    """An expectimax tree node."""

    view_state: GameViewState
    children: list[ExpectimaxTreeEdgeModel]


class ExpectimaxTreeInspectionModel(BaseModel, CamelCaseConfig):
    """Detailed inspection debugging data of the Expectimax game tree."""

    type: Literal["ExpectimaxTreeInspectionModel"]
    best_action: ActionModel
    tree_root: ExpectimaxTreeNodeModel


type GameTreeInspectionModel = Annotated[
    Union[
        MinimaxTreeInspectionModel,
        MctsTreeInspectionModel,
        ExpectimaxTreeInspectionModel,
    ],
    Field(discriminator="type"),
]
