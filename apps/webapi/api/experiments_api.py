from fastapi import APIRouter, Body
from webapi.models.experiment_models import (
    TranspositionTestRequest,
    TranspositionTestResponse,
    TreePayoffRequest,
    TreePayoffResponse,
)
from webapi.services.ai_service import AiService
from webapi.services.scene_service import SceneService

experiments_router = APIRouter(prefix="/api/rpc/experiment")


@experiments_router.post("/get-transposition-test")
async def get_transposition_test_result(
    body: TranspositionTestRequest = Body(...),
) -> TranspositionTestResponse:
    """Have AI perform an action and returns the mutated view state."""
    return AiService.get_transposition_test_result(body=body)


@experiments_router.post("/get-tree-payoff")
async def get_tree_payoff(
    body: TreePayoffRequest = Body(...),
) -> TreePayoffResponse:
    """Have AI perform an action and returns the mutated view state."""
    gs = SceneService.deserialize(body.state)
    return TreePayoffResponse(
        payoff_value=AiService.get_tree_payoff_value(gs),
    )
