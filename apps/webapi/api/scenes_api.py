from fastapi import APIRouter, Query
from webapi.models.state_models import SceneManifestResponse
from webapi.services.scene_service import SceneService

router = APIRouter(prefix="/api/scenes")


@router.get("/manifest")
async def get_scene_manifest() -> SceneManifestResponse:
    """Gets the scene manifest"""
    return SceneService.get_scenes()


@router.get("/json")
async def get_game_state_json(
    scene_names: list[str] = Query(..., alias="sceneNames"),
) -> str:
    """Gets a game state serialized entities table."""
    gs = SceneService.load_game_state(scene_names)
    return SceneService.serialize(gs, indent=False)
