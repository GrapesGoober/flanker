from fastapi import APIRouter, Body
from webapi.models.experiment_models import (
    TranspositionTestRequest,
    TranspositionTestResponse,
)
from webapi.services.ai_service import AiService

experiments_router = APIRouter(prefix="/api/rpc/experiment")


@experiments_router.post("/get-transposition-test")
async def get_transposition_test_result(
    body: TranspositionTestRequest = Body(...),
) -> TranspositionTestResponse:
    """Have AI perform an action and returns the mutated view state."""
    return AiService.get_transposition_test_result(body=body)
