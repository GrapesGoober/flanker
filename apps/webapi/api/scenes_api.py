from fastapi import APIRouter, Query
from webapi.models import SceneManifestResponse
from webapi.services.scene_service import SceneService

router = APIRouter(prefix="/api/scenes")


@router.get("")
async def get_scenes() -> SceneManifestResponse:
    """Gets a list of scenes."""
    return SceneService.get_scenes()


@router.get("/json")
async def get_game_state_json(
    scene_names: list[str] = Query(..., alias="sceneNames"),
) -> str:
    """Gets a game state serialized entities table."""
    gs = SceneService.load_game_state(scene_names)
    return SceneService.serialize(gs, indent=False)
