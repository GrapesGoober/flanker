import json

import requests
from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    url: str


def main() -> None:
    config = get_config()

    # r = requests.get(f"{config.url}/api/scenes")
    # print(r.text)

    scenes = [
        "experiment-settings",
        "experiment-scene-1",
        "experiment-blue-rh",
        "experiment-red-rh",
    ]

    r = requests.get(f"{config.url}/api/scenes/json", params={"sceneNames": scenes})
    scene_data = r.json()
    # print(scene_data)

    r = requests.post(f"{config.url}/api/ai-play", data=scene_data)
    print(r.json())


def get_config() -> ExperimentConfig:
    with open("./scripts/configs/experiment-config.json", "r") as f:
        return ExperimentConfig(**json.loads(f.read()))


if __name__ == "__main__":
    main()
