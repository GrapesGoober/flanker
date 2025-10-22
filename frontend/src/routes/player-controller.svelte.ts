import {
	GetTerrainData,
	GetUnitStatesData,
	performAssaultActionAsync,
	performFireActionAsync,
	performMoveActionAsync,
	type CombatUnitsViewState,
	type RifleSquadData,
	type TerrainModel,
	type Vec2
} from '$lib';

type PlayerControllerState =
	| { type: 'default' }
	| { type: 'selected'; selectedUnit: RifleSquadData }
	| { type: 'moveMarked'; selectedUnit: RifleSquadData; moveMarker: Vec2 }
	| { type: 'attackMarked'; selectedUnit: RifleSquadData; target: RifleSquadData };

export class PlayerController {
	terrainData: TerrainModel[] = $state([]);
	unitData: CombatUnitsViewState = $state({
		objectiveState: 'INCOMPLETE',
		hasInitiative: false,
		squads: []
	});
	isFetching: boolean = $state(false);
	state: PlayerControllerState = $state({ type: 'default' });

	async initializeAsync() {
		this.isFetching = true;
		this.terrainData = await GetTerrainData();
		this.unitData = await GetUnitStatesData();
		this.isFetching = false;
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
			type: 'attackMarked',
			target: target,
			selectedUnit: this.state.selectedUnit
		};
	}

	closeSelection() {
		this.state = {
			type: 'default'
		};
	}

	isMoveActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'moveMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.unitData.hasInitiative) return false;
		return true;
	}

	isFireActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'attackMarked') return false;
		if (this.state.selectedUnit.status === 'SUPPRESSED') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.unitData.hasInitiative) return false;
		return true;
	}

	isAssaultActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'attackMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.unitData.hasInitiative) return false;
		return true;
	}

	async moveActionAsync() {
		if (!this.isMoveActionValid()) return;
		if (this.state.type !== 'moveMarked') return false;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		this.unitData = await performMoveActionAsync(unitId, this.state.moveMarker);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	async fireActionAsync() {
		if (!this.isFireActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		this.unitData = await performFireActionAsync(unitId, this.state.target.unitId);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	async assaultActionAsync() {
		if (!this.isAssaultActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		this.unitData = await performAssaultActionAsync(unitId, this.state.target.unitId);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	private reselectUnit(unitId: number) {
		let currentUnit = this.unitData.squads.find((unit) => unit.unitId == unitId);
		if (currentUnit)
			this.state = {
				type: 'selected',
				selectedUnit: currentUnit
			};
		else this.state = { type: 'default' };
	}
}
