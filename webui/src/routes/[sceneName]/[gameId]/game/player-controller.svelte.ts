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
	| { type: 'attackMarked'; selectedUnit: RifleSquadData; target: RifleSquadData };

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
	errorMessage: string | null = $state(null);
	errorLog: string[] = $state([]);

	/* Initializes controller and loads terrain & unit states data. */
	async initializeAsync() {
		if (this.isFetching) return;
		this.isFetching = true;
		this.clearError();
		try {
			const [terrainData, unitData] = await Promise.all([GetTerrainData(), GetUnitStatesData()]);
			this.terrainData = terrainData;
			this.unitData = unitData;
		} catch (error) {
			this.reportError('Unable to load game state', error);
		} finally {
			this.isFetching = false;
		}
	}

	/* Selects a combat unit and transitions to state 'selected'. */
	selectUnit(unitId: string) {
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

	/* Clears currently shown error text. */
	clearError() {
		this.errorMessage = null;
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

	/* Returns true if pivot action is valid. */
	isPivotActionValid(): boolean {
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
		if (this.state.type !== 'moveMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		const moveMarker = this.state.moveMarker;
		await this.runActionAsync(unitId, () => performMoveActionAsync(unitId, moveMarker));
	}

	/* Performs pivot action for the selected unit. */
	async pivotActionAsync() {
		if (!this.isPivotActionValid()) return;
		if (this.state.type !== 'moveMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		const moveMarker = this.state.moveMarker;
		await this.runActionAsync(unitId, () => performPivotActionAsync(unitId, moveMarker));
	}

	/* Performs fire action for the selected unit. */
	async fireActionAsync() {
		if (!this.isFireActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		const targetId = this.state.target.unitId;
		await this.runActionAsync(unitId, () => performFireActionAsync(unitId, targetId));
	}

	/* Performs assault action for the selected unit. */
	async assaultActionAsync() {
		if (!this.isAssaultActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		const targetId = this.state.target.unitId;
		await this.runActionAsync(unitId, () => performAssaultActionAsync(unitId, targetId));
	}

	/* Executes an async unit action while keeping controller state recoverable on failure. */
	private async runActionAsync(
		unitId: string,
		action: () => Promise<CombatUnitsViewState>
	): Promise<void> {
		if (this.isFetching) return;
		this.isFetching = true;
		this.clearError();
		try {
			this.unitData = await action();
			this.reselectUnit(unitId);
		} catch (error) {
			this.reportError('Action failed', error);
		} finally {
			this.isFetching = false;
		}
	}

	/* Records error details for UI display while keeping the newest at the top. */
	private reportError(context: string, error: unknown) {
		const details =
			error instanceof Error ? error.message : typeof error === 'string' ? error : 'Unknown error';
		const message = `${context}. ${details}`;
		this.errorMessage = message;
		this.errorLog = [`${new Date().toLocaleTimeString()} ${message}`, ...this.errorLog].slice(0, 6);
	}

	/* Reselects the unit after an action, or resets state if not found. */
	private reselectUnit(unitId: string) {
		let currentUnit = this.unitData.squads.find((unit) => unit.unitId == unitId);
		if (currentUnit)
			this.state = {
				type: 'selected',
				selectedUnit: currentUnit
			};
		else this.state = { type: 'default' };
	}
}
