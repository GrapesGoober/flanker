import {
	GetTerrainData,
	GetUnitStatesData,
	MoveRifleSquad,
	type CombatUnitsData,
	type RifleSquadData,
	type TerrainFeatureData,
	type Vec2
} from '$lib';

export type PlayerStateContext = {
	terrainData: TerrainFeatureData[];
	unitData: CombatUnitsData;
	marker: Vec2 | null;
	selectedUnit: RifleSquadData | null;
};

export function newPlayerState(): PlayerStateContext {
	return {
		terrainData: [],
		unitData: {
			hasInitiative: false,
			squads: []
		},
		marker: null,
		selectedUnit: null
	};
}

export async function initializePlayerState(state: PlayerStateContext) {
	state.terrainData = await GetTerrainData();
	state.unitData = await GetUnitStatesData();
}

export function addMarker(state: PlayerStateContext, at: Vec2) {
	if (state.unitData.hasInitiative === false) {
		return;
	}

	if (state.selectedUnit === null) {
		return;
	}
	state.marker = at;
}

export async function moveToMarkerAsync(state: PlayerStateContext) {
	if (state.unitData.hasInitiative === false) return;
	if (state.selectedUnit === null) return;
	if (state.marker === null) return;

	state.unitData = await MoveRifleSquad(state.selectedUnit.unitId, state.marker);
	state.marker = null;
	state.selectedUnit = null;
}

export function selectUnit(state: PlayerStateContext, unitId: number) {
	if (state.marker != null) return;
	// Deselect all units, then select the correct one
	for (const unit of state.unitData.squads) {
		unit.isSelected = unit.unitId === unitId;
		if (unit.unitId == unitId && unit.isFriendly == true) {
			state.selectedUnit = unit;
		}
	}
}

export async function cancleMarker(state: PlayerStateContext) {
	state.marker = null;
}
