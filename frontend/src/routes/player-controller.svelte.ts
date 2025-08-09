import {
	getTerrainData,
	getUnitStatesData,
	performFireActionAsync,
	performMoveActionAsync,
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
		objectivesState: 'INCOMPLETE',
		hasInitiative: false,
		squads: []
	});

	state: PlayerControllerState = $state({ type: 'default' });

	async initializeAsync() {
		this.terrainData = await getTerrainData();
		this.unitData = await getUnitStatesData();
	}

	selectUnit(unitId: number) {
		let unit = this.unitData.squads.find((squad) => squad.unitId == unitId);
		if (!unit) return;
		if (unit.isFriendly === true) {
			this.state = {
				type: 'selected',
				selectedUnit: unit
			};
		}
		if (unit.isFriendly === false) {
			if (this.state.type === 'default') {
				this.state = {
					type: 'selected',
					selectedUnit: unit
				};
			} else this.setFireMarker(unit);
		}
	}

	setMoveMarker(at: Vec2) {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type == 'default') return;
		if (!this.state.selectedUnit.isFriendly) return;
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

	closeSelection() {
		this.state = {
			type: 'default'
		};
	}

	async confirmMarkerAsync() {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type === 'default') return;
		let unitId = this.state.selectedUnit.unitId;

		switch (this.state.type) {
			case 'moveMarked':
				if (!this.isMoveValid()) return;
				this.unitData = await performMoveActionAsync(unitId, this.state.moveMarker);
				break;
			case 'fireMarked':
				if (!this.isFireValid()) return;
				this.unitData = await performFireActionAsync(unitId, this.state.target.unitId);
				break;
		}

		// Reselect the unit again, if exists
		let currentUnit = this.unitData.squads.find((unit) => unit.unitId == unitId);
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

	isMoveValid(): boolean {
		if (this.state.type !== 'moveMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		return true;
	}

	isFireValid(): boolean {
		if (this.state.type !== 'fireMarked') return false;
		if (this.state.selectedUnit.status === 'SUPPRESSED') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		return true;
	}
}
