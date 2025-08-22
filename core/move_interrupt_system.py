from numba import njit  # type: ignore
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
from core.los_system import IntersectSystem
from core.utils.linear_transform import LinearTransform
from core.utils.vec2 import Vec2


class MoveInterruptSystem:

    @staticmethod
    def batch_interrupt_check(
        gs: GameState,
        unit_id: int,
        to: Vec2,
    ) -> list[tuple[int, int]]:
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

        move_coords = MoveInterruptSystem.get_move_steps(transform.position, to)
        spotter_ids, spotter_coords = MoveInterruptSystem.get_spotter(
            gs, hostile_faction
        )
        terrain_data = MoveInterruptSystem.compile_terrain(gs)
        # TODO: merge list[array] coordinates into just one large array
        # TODO: wanna try using parallel terrain IDs instead? Building these terrains are hard
        # TODO: let's do perftest first. Don't worry about see-in see-out logic yet
        interrupts = MoveInterruptSystem.get_interrupts(
            spotter_ids=spotter_ids,
            spotters=[
                np.array([v.x, v.y, 0], dtype=np.float64) for v in spotter_coords
            ],
            terrain=terrain_data,
            move_steps=list(
                [np.array([v.x, v.y, 0], dtype=np.float64) for v in move_coords]
            ),
        )
        return interrupts

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

        return spotters, coords

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
    def get_excluded_terrains(
        gs: GameState,
        spotter_ids: list[int],
    ) -> list[list[int]]:
        """
        gs.query all terrain data, prepare terrain arrays
          - masked OPAQUE
          - might prefer a call-level cache, say, context object
          - thus, per move action, there is n=hostile_count terrain datasets
        """
        terrains: list[list[int]] = []
        for terrain_id, terrain, _ in gs.query(TerrainFeature, Transform):
            if (terrain.flag & TerrainFeature.Flag.OPAQUE) == 0:
                continue
            new_terrain_ids: list[int] = []
            for ent_id in spotter_ids:
                if IntersectSystem.is_inside(gs, terrain_id, ent_id):
                    continue
                new_terrain_ids.append(terrain_id)
            terrains.append(new_terrain_ids)

        return terrains

    @staticmethod
    def compile_terrain(
        gs: GameState,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Compile terrain feature into numpy array for edges, per spotter."""

        # Compile each terrain's data, key=terrain_id, val=polygon array
        edge_sources: list[NDArray[np.float64]] = []
        edge_targets: list[NDArray[np.float64]] = []
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & TerrainFeature.Flag.OPAQUE) == 0:
                continue
            vertices = LinearTransform.apply(terrain.vertices, transform)
            # Explicitly tell numpy that we're working with 2d vectors with z=0
            poly = np.array([[v.x, v.y, 0] for v in vertices], dtype=np.float64)
            edge_sources.append(poly)
            edge_targets.append(np.roll(poly, shift=-1, axis=0))

        if edge_sources == [] or edge_targets == []:
            return (
                np.array([[0, 0, 0]], dtype=np.float64),
                np.array([[0, 0, 0]], dtype=np.float64),
            )
        edge_source = np.vstack(edge_sources)
        edge_target = np.vstack(edge_targets)
        return edge_source, edge_target

    @staticmethod
    @njit
    def get_interrupts(
        spotter_ids: list[int],
        spotters: list[NDArray[np.float64]],
        terrain: tuple[NDArray[np.float64], NDArray[np.float64]],
        move_steps: list[NDArray[np.float64]],
    ) -> list[tuple[int, int]]:
        """Returns list of interrupt, using (spotter_id, move_step index)"""
        interrupts: list[tuple[int, int]] = []
        for move_step_index, move_step in enumerate(move_steps):
            for i, spotter_id in enumerate(spotter_ids):
                spotter = spotters[i]
                edge_sources, edge_targets = terrain
                edge_vectors = edge_targets - edge_sources
                line_vector = move_step - spotter

                # Compute two parametric values t & u of intersect point
                line_cross_edge = np.cross(line_vector, edge_vectors)[:, 2]
                q1_p1 = edge_sources - spotter
                t = np.cross(q1_p1, edge_vectors)[:, 2] / line_cross_edge
                u = np.cross(q1_p1, line_vector)[:, 2] / line_cross_edge

                # parallel = np.isclose(line_cross_edge, 0)
                parallel = np.abs(line_cross_edge) <= 1e-8
                intersect_mask = (~parallel) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)

                if int(np.count_nonzero(intersect_mask)) <= 1:
                    interrupts.append((spotter_id, move_step_index))
        return interrupts
