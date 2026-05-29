import random
from typing import Sequence

from flanker_ai.actions import Action, AssaultAction, FireAction, MoveAction
from flanker_ai.components import InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.linear_transform import LinearTransform


class AiActionService:

    @staticmethod
    def get_actions(
        gs: GameState,
        initiative: InitiativeState.Faction,
    ) -> Sequence[Action]:
        boundary_vertices: list[Vec2] = []
        mask = TerrainFeature.Flag.BOUNDARY
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])
        min_x = int(min(v.x for v in boundary_vertices))
        max_x = int(max(v.x for v in boundary_vertices))
        min_y = int(min(v.y for v in boundary_vertices))
        max_y = int(max(v.y for v in boundary_vertices))

        # Generate an action for each combat unit
        actions: list[Action] = []
        for unit_id, unit in gs.query(CombatUnit):
            if unit.faction != initiative:
                continue

            pos = gs.get_component(unit_id, Transform).position
            actions.append(
                MoveAction(
                    unit_id=unit_id,
                    to=pos,
                )
            )
            for _ in range(10):
                rand_x = random.randrange(min_x, max_x)
                rand_y = random.randrange(min_y, max_y)
                vec = Vec2(rand_x, rand_y)
                actions.append(
                    MoveAction(
                        unit_id=unit_id,
                        to=vec,
                    )
                )

            # Fire and Assault actions for all permutations
            for target_id, target in gs.query(CombatUnit):
                if target.faction != initiative:
                    actions.append(
                        AssaultAction(
                            unit_id=unit_id,
                            target_id=target_id,
                        )
                    )
                    actions.append(
                        FireAction(
                            unit_id=unit_id,
                            target_id=target_id,
                        )
                    )

        return actions
