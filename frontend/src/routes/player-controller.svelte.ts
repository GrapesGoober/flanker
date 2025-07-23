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
	| { type: 'moveMarked'; selectedUnit: RifleSquadData; moveMarker: Vec2 }
	| { type: 'fireMarked'; selectedUnit: RifleSquadData; target: RifleSquadData };

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
		let unit = this.unitData.squads.find((squad) => squad.unitId == unitId);
		if (!unit) return;
		if (unit.isFriendly == true) {
			this.state = {
				type: 'selected',
				selectedUnit: unit
			};
		} else {
			// click on hostile => assume fire action
			this.setFireMarker(unit);
		}
	}

	setMoveMarker(at: Vec2) {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type == 'default') return;
		this.state = {
			type: 'moveMarked',
			moveMarker: at,
			selectedUnit: this.state.selectedUnit
		};
	}

	setFireMarker(target: RifleSquadData) {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type == 'default') return;
		if (target.isFriendly) return;
		this.state = {
			type: 'fireMarked',
			target: target,
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
		if (this.state.type != 'moveMarked') return;

		let selectedUnit = this.state.selectedUnit; // Avoid this binding shenanigans
		this.unitData = await MoveRifleSquad(selectedUnit.unitId, this.state.moveMarker);
		let currentUnit = this.unitData.squads.find((unit) => unit.unitId == selectedUnit.unitId);
		if (currentUnit)
			this.state = {
				type: 'selected',
				selectedUnit: currentUnit
			};
		else
			this.state = {
				type: 'default'
			};
	}
}
