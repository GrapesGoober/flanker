import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';
const client = createClient<paths>();

export type Vec2 = components['schemas']['Vec2'];

export type TerrainModel = components['schemas']['TerrainModel'];
export type CombatUnitsViewState = components['schemas']['CombatUnitsViewState'];
export type RifleSquadData = components['schemas']['SquadModel'];

export type MoveActionLog = components['schemas']['MoveActionLog'];
export type FireActionLog = components['schemas']['FireActionLog'];
export type AssaultActionLog = components['schemas']['AssaultActionLog'];
export type ActionLog = MoveActionLog | FireActionLog | AssaultActionLog;

const params = {
	path: {
		scene_name: 'demo',
		game_id: 0
	}
};

export async function GetTerrainData(): Promise<TerrainModel[]> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/terrain', {
		params
	});
	if (error) throw new Error(JSON.stringify(error));

	return data;
}

export async function UpdateTerrainData(terrain: TerrainModel) {
	const { data, error } = await client.PUT('/api/{scene_name}/{game_id}/terrain', {
		params,
		body: terrain
	});
	if (error) throw new Error(JSON.stringify(error));
}

export async function GetUnitStatesData(): Promise<CombatUnitsViewState> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/units', {
		params
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

export async function performMoveActionAsync(
	unit_id: number,
	to: Vec2
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/move', {
		params,
		body: {
			unitId: unit_id,
			to: to
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

export async function performFireActionAsync(
	unit_id: number,
	target_id: number
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/fire', {
		params,
		body: {
			unitId: unit_id,
			targetId: target_id
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

export async function performAssaultActionAsync(
	unit_id: number,
	target_id: number
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/assault', {
		params,
		body: {
			unitId: unit_id,
			targetId: target_id
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

export async function GetLogs(): Promise<ActionLog[]> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/logs', {
		params
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}
