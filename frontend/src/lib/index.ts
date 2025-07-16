import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';
const client = createClient<paths>();

export type Vec2 = { x: number; y: number };

export type TerrainFeatureData = {
	terrainType: 'FOREST' | 'ROAD' | 'FIELD' | 'WATER' | 'BUILDING';
	coordinates: Vec2[];
};

export async function GetTerrainData(): Promise<TerrainFeatureData[]> {
	const {
		data, // only present if 2XX response
		error // only present if 4XX or 5XX response
	} = await client.GET('/api/terrain');
	if (error) throw new Error(JSON.stringify(error));

	// Convert to a custom type in case API and types diverge
	const terrainData: TerrainFeatureData[] = data.map((element) => ({
		terrainType: element.terrain_type,
		coordinates: element.vertices
	}));

	return terrainData;
}

export type UnitStateData = {
	hasInitiative: boolean;
	squads: RifleSquadData[];
};

export type RifleSquadData = {
	isSelected: boolean;
	unitId: number;
	position: Vec2;
	status: 'ACTIVE' | 'PINNED' | 'SUPPRESSED';
	isFriendly: boolean;
};

function ParseUnitStatesData(data: components['schemas']['UnitState']): UnitStateData {
	return {
		hasInitiative: data.has_initiative,
		squads: data.squads.map((squad) => ({
			isSelected: false,
			unitId: squad.unit_id,
			position: squad.position,
			status: squad.status,
			isFriendly: squad.is_friendly
		}))
	};
}

export async function GetUnitStatesData(): Promise<UnitStateData> {
	const {
		data, // only present if 2XX response
		error // only present if 4XX or 5XX response
	} = await client.GET('/api/rifle-squad');
	if (error) throw new Error(JSON.stringify(error));

	// Convert to a custom type in case API and types diverge
	return ParseUnitStatesData(data);
}

export async function MoveRifleSquad(unit_id: number, to: Vec2): Promise<UnitStateData> {
	const {
		data, // only present if 2XX response
		error // only present if 4XX or 5XX response
	} = await client.POST('/api/move', {
		body: {
			unit_id: unit_id,
			to: to
		}
	});
	if (error) throw new Error(JSON.stringify(error));

	// Convert to a custom type in case API and types diverge
	return ParseUnitStatesData(data);
}
