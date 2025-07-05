from core.command import Command
from core.gamestate import GameState
from core.components import CommandUnit


class BasicAi:

    @staticmethod
    def play(gs: GameState, parent_commander_id: int) -> None:
        if not (command := gs.get_component(parent_commander_id, CommandUnit)):
            return
        if command.has_initiative == False:
            return

        # Pass on initiative without any actions
        Command.flip_initiative(gs)
