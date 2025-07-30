from core.gamestate import GameState

from backend.scene import new_scene

# context = new_scene()
# json_str = context.gs.save()
# print(json_str)

with open("entities.json", "r") as f:
    gs = GameState.load(f.read())

with open("entities.json", "w") as f:
    f.write(gs.save())
