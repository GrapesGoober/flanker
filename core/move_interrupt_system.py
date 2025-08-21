import numpy as np
from numpy.typing import NDArray
from core.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    TerrainFeature,
    Transform,
)
from core.gamestate import GameState
from core.utils.linear_transform import LinearTransform
from core.utils.vec2 import Vec2


class MoveInterruptSystem:

    @staticmethod
    def batch_interrupt_check(gs: GameState, unit_id: int, to: Vec2) -> None:
        # STEP 1
        # Generate arrays of source and target points, [a] and [b]
        # STEP 2
        # gs.query all terrain data, prepare terrain arrays
        #   - masked OPAQUE
        #   - might prefer a call-level cache, say, context object
        #   - thus, per move action, there is n=hostile_count terrain datasets
        # STEP 3
        # pass this to separate njit func to process all arrays
        #   - python loops are possible, since njit can compile that
        #   - doesn't need all operations done in numpy's loop
        #   - return the index (either as np mask or py loop)
        #   - this index can be used to infer the interrupted position
        #
        # Might wanna try using cuda too once batch processing is done

        unit = gs.get_component(unit_id, CombatUnit)
        transform = gs.get_component(unit_id, Transform)

        match unit.faction:
            case InitiativeState.Faction.BLUE:
                hostile_faction = InitiativeState.Faction.RED
            case InitiativeState.Faction.RED:
                hostile_faction = InitiativeState.Faction.BLUE

        _, spotter_coords = MoveInterruptSystem.get_spotter(gs, hostile_faction)
        move_coords = MoveInterruptSystem.get_move_steps(transform.position, to)
        edge_source, edge_vectors = MoveInterruptSystem.get_terrains(gs)

    @staticmethod
    def get_spotter(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> tuple[list[int], list[Vec2]]:

        spotters: list[int] = []
        coords: list[Vec2] = []
        for spotter_id, spotter_unit, transform, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):
            if spotter_unit.faction != faction:
                continue
            if fire_controls.can_reactive_fire == False:
                continue

            spotters.append(spotter_id)
            coords.append(transform.position)

        return [], []

    @staticmethod
    def get_move_steps(start: Vec2, to: Vec2) -> list[Vec2]:
        coords: list[Vec2] = []
        STEP_SIZE = 1
        delta = to - start
        length = delta.length()
        direction = delta.normalized()

        steps = int(length / STEP_SIZE)
        for i in range(steps):
            pos = start + direction * STEP_SIZE * i
            coords.append(pos)

        # Add the final position if not already added
        if length % STEP_SIZE != 0:
            coords.append(to)

        return coords

    @staticmethod
    def get_terrains(
        gs: GameState,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        edge_sources: list[NDArray[np.float64]] = []
        edge_targets: list[NDArray[np.float64]] = []
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & TerrainFeature.Flag.OPAQUE:
                vertices = LinearTransform.apply(terrain.vertices, transform)
                # Explicitly tell numpy that we're working with 2d vectors with z=0
                poly = np.array([[v.x, v.y, 0] for v in vertices], dtype=np.float64)
                shifted_poly = np.roll(poly, shift=-1, axis=0)
                edge_sources.append(poly)
                edge_targets.append(shifted_poly)

        if edge_sources == [] or edge_targets == []:
            return (
                np.array([[0, 0, 0]], dtype=np.float64),
                np.array([[0, 0, 0]], dtype=np.float64),
            )
        edge_source = np.vstack(edge_sources)
        edge_target = np.vstack(edge_targets)
        edge_vectors = edge_target - edge_source

        return edge_source, edge_vectors
