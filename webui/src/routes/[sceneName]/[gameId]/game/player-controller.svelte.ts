import {
	GetTerrainData,
	GetUnitStatesData,
	performAssaultActionAsync,
	performFireActionAsync,
	performMoveActionAsync,
	performPivotActionAsync,
	type CombatUnitsViewState,
	type RifleSquadData,
	type TerrainModel,
	type Vec2
} from '$lib/api';

type PlayerControllerState =
	| { type: 'default' }
	| { type: 'selected'; selectedUnit: RifleSquadData }
	| { type: 'moveMarked'; selectedUnit: RifleSquadData; moveMarker: Vec2 }
	| { type: 'attackMarked'; selectedUnit: RifleSquadData; target: RifleSquadData }
	| { type: 'pivoting'; selectedUnit: RifleSquadData };

/*
PlayerController class
Manages player state, unit selection, actions (move, fire, assault), and game data fetching.
Handles validation and updates for gameplay interactions.
*/
export class PlayerController {
	terrainData: TerrainModel[] = $state([]);
	unitData: CombatUnitsViewState = $state({
		objectiveState: 'INCOMPLETE',
		hasInitiative: false,
		squads: []
	});
	isFetching: boolean = $state(false);
	state: PlayerControllerState = $state({ type: 'default' });

	/* Initializes controller and loads terrain & unit states data. */
	async initializeAsync() {
		this.isFetching = true;
		this.terrainData = await GetTerrainData();
		this.unitData = await GetUnitStatesData();
		this.isFetching = false;
	}

	/* Selects a combat unit and transitions to state 'selected'. */
	selectUnit(unitId: number) {
		const unit = this.unitData.squads.find((squad) => squad.unitId == unitId);
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
			} else this.setAttackMarker(unit);
		}
	}

	/* Set move marker and transition state to 'moveMarked'. */
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

	/* Begin pivot mode for selected unit. */
	startPivoting() {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type !== 'selected') return;
		if (!this.state.selectedUnit.isFriendly) return;
		this.state = {
			type: 'pivoting',
			selectedUnit: this.state.selectedUnit,
		};
	}

	/* Sets aan marker for the selected unit then transition to 'attackMarked'. */
	setAttackMarker(target: RifleSquadData) {
		if (!this.unitData.hasInitiative) return;
		if (this.state.type == 'default') return;
		if (target.isFriendly) return;
		this.state = {
			type: 'attackMarked',
			target: target,
			selectedUnit: this.state.selectedUnit
		};
	}

	/* Closes the current selection and resets state. */
	closeSelection() {
		this.state = {
			type: 'default'
		};
	}

	/* Handles pivot action after a marker coordinate is chosen. */
	async pivotActionAsync(mousePos: Vec2) {
		if (this.isFetching) return;
		if (this.state.type !== 'pivoting') return;
		const unitId = this.state.selectedUnit.unitId;
		// compute heading from unit to clicked point
		const sel = this.state.selectedUnit;
		const dx = mousePos.x - sel.position.x;
		const dy = mousePos.y - sel.position.y;
		const deg = (Math.atan2(dy, dx) * 180) / Math.PI;
		let heading = deg;
		if (heading < 0) heading += 360;
		this.isFetching = true;
		this.unitData = await performPivotActionAsync(unitId, heading);
		this.isFetching = false;
		// return to selected state
		const current = this.unitData.squads.find((u) => u.unitId == unitId);
		if (current) {
			this.state = {
				type: 'selected',
				selectedUnit: current
			};
		} else {
			this.state = { type: 'default' };
		}
	}

	/* Returns true if move action is valid. */
	isMoveActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'moveMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.unitData.hasInitiative) return false;
		return true;
	}

	/* Returns true if fire action is valid. */
	isFireActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'attackMarked') return false;
		if (this.state.selectedUnit.status === 'SUPPRESSED') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.unitData.hasInitiative) return false;
		return true;
	}

	/* Returns true if assault action is valid. */
	isAssaultActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'attackMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.unitData.hasInitiative) return false;
		return true;
	}

	/* Performs move action for the selected unit. */
	async moveActionAsync() {
		if (!this.isMoveActionValid()) return;
		if (this.state.type !== 'moveMarked') return false;
		const unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		this.unitData = await performMoveActionAsync(unitId, this.state.moveMarker);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Performs fire action for the selected unit. */
	async fireActionAsync() {
		if (!this.isFireActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		const unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		this.unitData = await performFireActionAsync(unitId, this.state.target.unitId);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Performs assault action for the selected unit. */
	async assaultActionAsync() {
		if (!this.isAssaultActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		const unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		this.unitData = await performAssaultActionAsync(unitId, this.state.target.unitId);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Reselects the unit after an action, or resets state if not found. */
	private reselectUnit(unitId: number) {
		const currentUnit = this.unitData.squads.find((unit) => unit.unitId == unitId);
		if (currentUnit)
			this.state = {
				type: 'selected',
				selectedUnit: currentUnit
			};
		else this.state = { type: 'default' };
	}
}
