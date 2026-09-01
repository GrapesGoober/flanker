import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import requests
from flanker_core.models.components import InitiativeState
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AiMatchResponse(BaseModel, CamelCaseConfig):
    """Response model from WebAPI."""

    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class ExperimentConfig(BaseModel):
    url: str
    scenes: list[str]
    parallelization: int
    size_to_run: int


@dataclass
class AiPlayRequest:
    config: ExperimentConfig
    scene_data: str


def main() -> None:
    config = get_config()

    # r = requests.get(f"{config.url}/api/scenes")
    # print(r.text)

    r = requests.get(
        f"{config.url}/api/scenes/json",
        params={"sceneNames": config.scenes},
    )
    scene_data = r.json()

    requests_to_send = [
        AiPlayRequest(
            config=config,
            scene_data=scene_data,
        )
        for _ in range(config.size_to_run)
    ]

    with ThreadPoolExecutor(
        max_workers=config.parallelization,
    ) as executor:
        for result in executor.map(
            send_ai_play_request,
            requests_to_send,
        ):
            response = AiMatchResponse(**result.json())
            print(response)


def get_config() -> ExperimentConfig:
    with open("./scripts/configs/experiment-config.json", "r") as f:
        return ExperimentConfig(**json.loads(f.read()))


def send_ai_play_request(
    request: AiPlayRequest,
) -> requests.Response:
    print("running!")
    r = requests.post(
        f"{request.config.url}/api/ai-play",
        data=request.scene_data,
    )
    if 300 <= r.status_code <= 600:
        raise Exception(f"Request had {r.status_code} error: {r.text}")
    return r


if __name__ == "__main__":
    main()
