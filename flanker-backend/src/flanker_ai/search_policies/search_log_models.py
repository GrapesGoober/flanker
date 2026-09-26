from dataclasses import dataclass


@dataclass
class RandomSearchLog:
    actions_length: int


@dataclass
class ExpectimaxSearchLog:
    tree_size: int


@dataclass
class MctsSearchLog:
    tree_depth: int


@dataclass
class RandomHeuristicLog:
    actions_length: int


@dataclass
class MinimaxSearchLog:
    tree_size: int


AiSearchLog = (
    MinimaxSearchLog
    | MctsSearchLog
    | ExpectimaxSearchLog
    | RandomHeuristicLog
    | RandomSearchLog
)
