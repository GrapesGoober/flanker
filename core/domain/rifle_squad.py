from systems.event import EventSystem, Listener
from systems.ecs import Entity, GameState
from systems.polygon import PolygonSpace
from systems.vec2 import Vec2
from domain.terrain import TerrainFlag
from domain.interface import (
    UnitState,
    MoveActionInput,
    RifleSquadGetInput,
    LosCheckEvent,
)


class RifleSquad(Entity):

    def __init__(self, gs: GameState, position: Vec2) -> None:
        self.position = position
        self.state = UnitState.ACTIVE
        super().__init__(
            gs,
            Listener(MoveActionInput, self.on_move),
            Listener(RifleSquadGetInput, self.on_get),
            Listener(LosCheckEvent, self.on_get_los),
        )

    def on_get(self, e: RifleSquadGetInput) -> RifleSquadGetInput.Response:
        return RifleSquadGetInput.Response(
            unit_id=hash(self), position=self.position, state=self.state
        )

    def on_get_los(self, event: LosCheckEvent) -> LosCheckEvent.Response | None:
        if event.parent_id == hash(self):
            return
        intersects = self.gs.system(PolygonSpace).get_intersects(
            start=event.position, end=self.position, mask=TerrainFlag.OPAQUE
        )
        if list(intersects) == []:
            return LosCheckEvent.Response(parent_id=hash(self))
        return None

    def on_move(self, e: MoveActionInput) -> None:
        if e.unit_id != hash(self):
            return
        if self.state != UnitState.ACTIVE:
            return

        to = e.position
        # First, check that move is valid through WALKABLE flag
        for i in self.gs.system(PolygonSpace).get_intersects(self.position, to):
            if not (i.feature.flag & TerrainFlag.WALKABLE):
                return

        # Then, check LoS interrupt along the movement line segment
        STEP_SIZE = 0.1
        length = (to - self.position).length()
        direction = (to - self.position) / length
        for i in range(int(length / STEP_SIZE) + 1):
            point = self.position + direction * (STEP_SIZE * i)
            los: list[LosCheckEvent.Response] = self.gs.system(EventSystem).emit(
                LosCheckEvent(parent_id=hash(self), position=point),
                response_type=LosCheckEvent.Response,
            )
            if los:  # Spotted, stop right there
                self.position = point
                self.state = UnitState.SUPPRESSED
                return

        # Not spotted, move to destination
        self.position = to
