from dataclasses import dataclass

from flanker_core.models.components import InitiativeState


@dataclass
class RandomSearchLog:
    faction: InitiativeState.Faction
    actions_length: int


@dataclass
class ExpectimaxSearchLog:
    faction: InitiativeState.Faction
    tree_size: int


@dataclass
class MctsSearchLog:
    faction: InitiativeState.Faction
    tree_depth: int


@dataclass
class RandomHeuristicLog:
    faction: InitiativeState.Faction
    actions_length: int


@dataclass
class MinimaxSearchLog:
    faction: InitiativeState.Faction
    tree_size: int


AiSearchLog = (
    MinimaxSearchLog
    | MctsSearchLog
    | ExpectimaxSearchLog
    | RandomHeuristicLog
    | RandomSearchLog
)
