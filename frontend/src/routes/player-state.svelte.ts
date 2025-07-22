import {
	GetTerrainData,
	GetUnitStatesData,
	MoveRifleSquad,
	type CombatUnitsData,
	type RifleSquadData,
	type TerrainFeatureData,
	type Vec2
} from '$lib';

export class PlayerState {
	terrainData: TerrainFeatureData[] = $state([]);
	unitData: CombatUnitsData = $state({
		hasInitiative: false,
		squads: []
	});
	moveMarker: Vec2 | null = $state(null);
	selectedUnit: RifleSquadData | null = $state(null);

	async initializeAsync() {
		this.terrainData = await GetTerrainData();
		this.unitData = await GetUnitStatesData();
	}

	addMoveMarker(at: Vec2) {
		if (!this.unitData.hasInitiative) return;
		if (this.selectedUnit === null) return;
		this.moveMarker = at;
	}

	async moveToMarkerAsync() {
		if (!this.unitData.hasInitiative) return;
		if (this.selectedUnit === null) return;
		if (this.moveMarker === null) return;

		this.unitData = await MoveRifleSquad(this.selectedUnit.unitId, this.moveMarker);
		this.moveMarker = null;
		this.selectedUnit = null;
	}

	selectUnit(unitId: number) {
		if (this.moveMarker != null) return;

		for (const unit of this.unitData.squads) {
			unit.isSelected = unit.unitId === unitId;
			if (unit.unitId === unitId && unit.isFriendly === true) {
				this.selectedUnit = unit;
			}
		}
	}

	cancelMarker() {
		this.moveMarker = null;
	}
}
