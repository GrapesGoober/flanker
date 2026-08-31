import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import requests
from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    url: str


@dataclass
class AiPlayRequest:
    config: ExperimentConfig
    scene_data: str


def main() -> None:
    config = get_config()

    # r = requests.get(f"{config.url}/api/scenes")
    # print(r.text)

    scenes = [
        "experiment-settings",
        "experiment-scene-1",
        "experiment-blue-analysis",
        "experiment-red-analysis",
    ]

    r = requests.get(f"{config.url}/api/scenes/json", params={"sceneNames": scenes})
    scene_data = r.json()

    WORKERS = 10

    requests_to_send = [
        AiPlayRequest(
            config=config,
            scene_data=scene_data,
        )
        for _ in range(WORKERS)
    ]

    with ThreadPoolExecutor(max_workers=len(requests_to_send)) as executor:
        for result in executor.map(
            send_ai_play_request,
            requests_to_send,
        ):
            print(result.json())


def get_config() -> ExperimentConfig:
    with open("./scripts/configs/experiment-config.json", "r") as f:
        return ExperimentConfig(**json.loads(f.read()))


def send_ai_play_request(request: AiPlayRequest) -> requests.Response:
    r = requests.post(
        f"{request.config.url}/api/ai-play",
        data=request.scene_data,
    )
    r.raise_for_status()
    return r


if __name__ == "__main__":
    main()
