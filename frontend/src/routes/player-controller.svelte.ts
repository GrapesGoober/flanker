import {
	GetTerrainData,
	GetUnitStatesData,
	MoveRifleSquad,
	type CombatUnitsData,
	type RifleSquadData,
	type TerrainFeatureData,
	type Vec2
} from '$lib';

type PlayerControllerState =
	| { type: 'default' }
	| { type: 'selected'; selectedUnit: RifleSquadData }
	| { type: 'marked'; selectedUnit: RifleSquadData; moveMarker: Vec2 };

export class PlayerController {
	terrainData: TerrainFeatureData[] = $state([]);
	unitData: CombatUnitsData = $state({
		hasInitiative: false,
		squads: []
	});

	state: PlayerControllerState = $state({ type: 'default' });

	async initializeAsync() {
		this.terrainData = await GetTerrainData();
		this.unitData = await GetUnitStatesData();
	}

	selectUnit(unitId: number) {
		if (this.state.type != 'default') return;
		let unit = this.unitData.squads.find((squad) => squad.unitId == unitId);
		if (!unit) return;
		if (unit.isFriendly !== true) return;
		this.state = {
			type: 'selected',
			selectedUnit: unit
		};
	}

	setMoveMarker(at: Vec2) {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type == 'default') return;
		this.state = {
			type: 'marked',
			moveMarker: at,
			selectedUnit: this.state.selectedUnit
		};
	}

	cancelMarker() {
		this.state = {
			type: 'default'
		};
	}

	async moveToMarkerAsync() {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type != 'marked') return;

		this.unitData = await MoveRifleSquad(this.state.selectedUnit.unitId, this.state.moveMarker);
		this.state = {
			type: 'default'
		};
	}
}
