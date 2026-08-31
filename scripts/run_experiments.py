import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import requests
from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    url: str
    scenes: list[str]
    parallelization: int


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
        for _ in range(config.parallelization)
    ]

    with ThreadPoolExecutor(
        max_workers=len(requests_to_send),
    ) as executor:
        for _ in executor.map(
            send_ai_play_request,
            requests_to_send,
        ):
            print("done!")
            # print(result.json())


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
    r.raise_for_status()
    return r


if __name__ == "__main__":
    main()
