export enum TerrainType {
	Forest = 'FOREST',
	Road = 'ROAD',
	Field = 'FIELD',
	Water = 'WATER',
	Building = 'BUILDING',
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

	const terrainData: TerrainFeatureData[] = resData.map((data) => ({
		terrain_type: data.terrain_type,
		coordinates: data.vertices.map((v) => ({
			x: v.x,
			y: v.y
		}))
	}));

	return terrainData;
}

export type UnitStateData = {
	hasInitiative: boolean;
	squads: RifleSquadData[];
}

export enum UnitState {
	Active = 'ACTIVE',
	Pinned = 'PINNED',
	Suppressed = 'SUPPRESSED'
}

export type RifleSquadData = {
	isSelected: boolean;
	unitId: number;
	position: Vec2;
	state: UnitState;
	isFriendly: boolean;
};

async function ParseUnitStatesData(res: Response): Promise<UnitStateData> {
	const resData: {
		has_initiative: boolean;
		squads: {
			unit_id: number;
			position: Vec2;
			status: UnitState;
			is_friendly: boolean;	
		}[];
	} = await res.json();

	const unitState: UnitStateData = {
		hasInitiative: resData.has_initiative,
		squads: resData.squads.map((data) => ({
			isSelected: false,
			unitId: data.unit_id,
			position: data.position,
			state: data.status,
			isFriendly: data.is_friendly
		}))
	}

	return unitState;
}

export async function GetUnitStatesData(): Promise<UnitStateData> {
	const res = await fetch('/api/rifle-squad');
	if (!res.ok) throw new Error('Failed to fetch rifle squads');
	return await ParseUnitStatesData(res);
}

export async function MoveRifleSquad(unit_id: number, to: Vec2): Promise<UnitStateData> {
	const res = await fetch('/api/move', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			unit_id,
			to
		})
	});
	if (!res.ok) throw new Error('Failed to move rifle squad');
	return await ParseUnitStatesData(res);
}
