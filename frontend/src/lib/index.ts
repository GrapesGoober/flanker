export enum TerrainType {
	Forest = 'FOREST',
	Road = 'ROAD',
	Field = 'FIELD',
	Water = 'WATER',
	Undefined = 0
}

export type Vec2 = { x: number; y: number };

export type TerrainFeatureData = {
	terrain_type: TerrainType;
	coordinates: Vec2[];
};

export async function GetTerrainData(): Promise<TerrainFeatureData[]> {
	const res = await fetch('/api/terrain');
	if (!res.ok) throw new Error('Failed to fetch terrain');

	const resData: {
		feature_id: number;
		vertices: Vec2[];
		terrain_type: TerrainType;
	}[] = await res.json();

	resData.forEach((data) => {
		const err = new Error('Terrain response data invalid');
		if (
			typeof data !== 'object' ||
			data === null ||
			typeof data.feature_id !== 'number' ||
			!Array.isArray(data.vertices) ||
			typeof data.terrain_type !== 'string'
		) {
			throw err;
		}
	});

	const terrainData: TerrainFeatureData[] = resData.map((data) => ({
		terrain_type: data.terrain_type,
		coordinates: data.vertices.map((v) => ({
			x: v.x,
			y: v.y
		}))
	}));

	return terrainData;
}

export enum UnitState {
	Active = 'ACTIVE',
	Suppressed = 'SUPPRESSED'
}

export type RifleSquadData = {
	unit_id: number;
	position: Vec2;
	state: UnitState;
};

export async function GetRifleSquadsData(): Promise<RifleSquadData[]> {
	const res = await fetch('/api/rifle-squad');
	if (!res.ok) throw new Error('Failed to fetch rifle squads');

	const resData: {
		unit_id: number;
		position: Vec2;
		status: UnitState;
	}[] = await res.json();

	resData.forEach((data) => {
		const err = new Error('Units response data invalid');
		if (
			typeof data !== 'object' ||
			data === null ||
			typeof data.unit_id !== 'number' ||
			typeof data.position !== 'object' ||
			typeof data.status !== 'string'
		) {
			throw err;
		}
	});

	const units: RifleSquadData[] = resData.map((data) => ({
		unit_id: data.unit_id,
		position: data.position,
		state: data.status
	}));

	return units;
}
