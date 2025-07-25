import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';
const client = createClient<paths>();

export type Vec2 = { x: number; y: number };

export type TerrainFeatureData = {
	terrainType: 'FOREST' | 'ROAD' | 'FIELD' | 'WATER' | 'BUILDING';
	coordinates: Vec2[];
};

export async function getTerrainData(): Promise<TerrainFeatureData[]> {
	const { data, error } = await client.GET('/api/terrain');
	if (error) throw new Error(JSON.stringify(error));

	// Convert to a custom type in case API and types diverge
	const terrainData: TerrainFeatureData[] = data.map((element) => ({
		terrainType: element.terrain_type,
		coordinates: element.vertices
	}));

	return terrainData;
}

export type CombatUnitsData = {
	hasInitiative: boolean;
	squads: RifleSquadData[];
};

export type RifleSquadData = {
	unitId: number;
	position: Vec2;
	status: 'ACTIVE' | 'PINNED' | 'SUPPRESSED';
	isFriendly: boolean;
	noFire: boolean;
};

function ParseUnitStatesData(data: components['schemas']['CombatUnitsViewState']): CombatUnitsData {
	return {
		hasInitiative: data.has_initiative,
		squads: data.squads.map((squad) => ({
			unitId: squad.unit_id,
			position: squad.position,
			status: squad.status,
			isFriendly: squad.is_friendly,
			noFire: squad.no_fire
		}))
	};
}

export async function getUnitStatesData(): Promise<CombatUnitsData> {
	const { data, error } = await client.GET('/api/units');
	if (error) throw new Error(JSON.stringify(error));
	return ParseUnitStatesData(data);
}

export async function performMoveActionAsync(unit_id: number, to: Vec2): Promise<CombatUnitsData> {
	const { data, error } = await client.POST('/api/move', {
		body: {
			unit_id: unit_id,
			to: to
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return ParseUnitStatesData(data);
}

export async function performFireActionAsync(
	unit_id: number,
	target_id: number
): Promise<CombatUnitsData> {
	const { data, error } = await client.POST('/api/fire', {
		body: {
			unit_id: unit_id,
			target_id: target_id
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return ParseUnitStatesData(data);
}
