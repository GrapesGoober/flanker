from typing import Literal

from pydantic import BaseModel


class TranspositionExperimentSetConfig(BaseModel):
    """Input config model for entire transposition experiment-set run."""

    iterations: int
    max_workers: int
    target: Literal["local"] | str
