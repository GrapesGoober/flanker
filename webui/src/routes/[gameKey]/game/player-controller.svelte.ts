import {
	GetTerrainData,
	GetUnitStatesData,
	performActionAsync,
	type GameViewState,
	type RifleSquadData,
	type TerrainModel,
	type Vec2
} from '$lib/api';
import { loadGameLocal, saveGameLocal } from '$lib/scenes-storage';

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
	viewState: GameViewState = $state({
		objectiveState: 'INCOMPLETE',
		hasInitiative: false,
		squads: []
	});
	isFetching: boolean = $state(false);
	state: PlayerControllerState = $state({ type: 'default' });
	gameKey: string = $state('');

	getGameStateJson(): string {
		const gameStateJson = loadGameLocal(this.gameKey);
		return gameStateJson;
	}

	updateGameStateJson(gameStateJson: string) {
		saveGameLocal(this.gameKey, gameStateJson);
	}

	/* Initializes controller and loads terrain & unit states data. */
	async initializeAsync(gameKey: string) {
		this.gameKey = gameKey;
		this.isFetching = true;
		const gameStateJson = this.getGameStateJson();
		this.terrainData = await GetTerrainData(gameStateJson);
		this.viewState = await GetUnitStatesData(gameStateJson);
		this.isFetching = false;
	}

	/* Selects a combat unit and transitions to state 'selected'. */
	selectUnit(unitId: string) {
		let unit = this.viewState.squads.find((squad) => squad.unitId == unitId);
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
			} else if (this.state.type == 'selected' && this.state.selectedUnit.isFriendly) {
				this.setAttackMarker(unit);
			}
		}
	}

	/* Set move marker and transition state to 'moveMarked'. */
	setMoveMarker(at: Vec2) {
		if (!this.viewState.hasInitiative) return;
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
		if (!this.viewState.hasInitiative) return;
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

	/* Returns true if move action is valid. */
	isMoveActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'moveMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.viewState.hasInitiative) return false;
		return true;
	}

	/* Returns true if pivot action is valid. */
	isPivotActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'moveMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.viewState.hasInitiative) return false;
		return true;
	}

	/* Returns true if fire action is valid. */
	isFireActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'attackMarked') return false;
		if (this.state.selectedUnit.status === 'SUPPRESSED') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.viewState.hasInitiative) return false;
		return true;
	}

	/* Returns true if assault action is valid. */
	isAssaultActionValid(): boolean {
		if (this.isFetching) return false;
		if (this.state.type !== 'attackMarked') return false;
		if (this.state.selectedUnit.status !== 'ACTIVE') return false;
		if (!this.state.selectedUnit.isFriendly) return false;
		if (!this.viewState.hasInitiative) return false;
		return true;
	}

	/* Performs move action for the selected unit. */
	async moveActionAsync() {
		if (!this.isMoveActionValid()) return;
		if (this.state.type !== 'moveMarked') return false;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		const gameStateJson = this.getGameStateJson();
		const result = await performActionAsync(gameStateJson, {
			actionType: 'MoveActionRequest',
			unitId: unitId,
			to: this.state.moveMarker
		});
		this.viewState = result.viewState;
		this.updateGameStateJson(result.jsonState);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Performs pivot action for the selected unit. */
	async pivotActionAsync() {
		if (!this.isPivotActionValid()) return;
		if (this.state.type !== 'moveMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		const gameStateJson = this.getGameStateJson();
		const result = await performActionAsync(gameStateJson, {
			actionType: 'PivotActionRequest',
			unitId: unitId,
			to: this.state.moveMarker
		});
		this.viewState = result.viewState;
		this.updateGameStateJson(result.jsonState);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Performs fire action for the selected unit. */
	async fireActionAsync() {
		if (!this.isFireActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		const gameStateJson = this.getGameStateJson();
		const result = await performActionAsync(gameStateJson, {
			actionType: 'FireActionRequest',
			unitId: unitId,
			targetId: this.state.target.unitId
		});
		this.viewState = result.viewState;
		this.updateGameStateJson(result.jsonState);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Performs assault action for the selected unit. */
	async assaultActionAsync() {
		if (!this.isAssaultActionValid()) return;
		if (this.state.type !== 'attackMarked') return;
		let unitId = this.state.selectedUnit.unitId;
		this.isFetching = true;
		const gameStateJson = this.getGameStateJson();
		const result = await performActionAsync(gameStateJson, {
			actionType: 'AssaultActionRequest',
			unitId: unitId,
			targetId: this.state.target.unitId
		});
		this.viewState = result.viewState;
		this.updateGameStateJson(result.jsonState);
		this.isFetching = false;
		this.reselectUnit(unitId);
	}

	/* Reselects the unit after an action, or resets state if not found. */
	private reselectUnit(unitId: string) {
		let currentUnit = this.viewState.squads.find((unit) => unit.unitId == unitId);
		if (currentUnit)
			this.state = {
				type: 'selected',
				selectedUnit: currentUnit
			};
		else this.state = { type: 'default' };
	}
}
