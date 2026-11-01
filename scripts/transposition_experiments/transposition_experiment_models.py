from typing import Literal

from pydantic import BaseModel


class TranspositionExperimentSetConfig(BaseModel):
    """Input config model for entire transposition experiment-set run."""

    n_tests: int
    state_populating_method: Literal["random"]
    max_workers: int
    target: Literal["local"] | str
