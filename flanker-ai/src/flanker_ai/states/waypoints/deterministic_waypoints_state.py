from typing import override
from uuid import UUID

from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.models.outcomes import FireOutcomes


class DeterministicWaypointsState(WaypointsState):

    @override
    def get_all_fire_permutations(
        self,
        enemy_ids: list[UUID],
    ) -> list[tuple[float, dict[UUID, FireOutcomes]]]:
        if len(enemy_ids) == 1:
            all_pins = {enemy_id: FireOutcomes.PIN for enemy_id in enemy_ids}
            return [(1, all_pins)]
        # It should avoid being pinned by more than one enemy
        # by assuming it gets suppressed
        if len(enemy_ids) > 1:
            one_pins = {enemy_id: FireOutcomes.SUPPRESS for enemy_id in enemy_ids}
            one_pins[enemy_ids[0]] = FireOutcomes.PIN
            return [(1, one_pins)]
        return []
