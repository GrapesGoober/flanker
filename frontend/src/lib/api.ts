import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';
import { page } from '$app/state';
const client = createClient<paths>();

export type Vec2 = components['schemas']['Vec2'];

export type TerrainModel = components['schemas']['TerrainModel'];
export type CombatUnitsViewState = components['schemas']['CombatUnitsViewState'];
export type RifleSquadData = components['schemas']['SquadModel'];

export type MoveActionLog = components['schemas']['MoveActionLog'];
export type FireActionLog = components['schemas']['FireActionLog'];
export type AssaultActionLog = components['schemas']['AssaultActionLog'];
export type ActionLog = MoveActionLog | FireActionLog | AssaultActionLog;

export type RouteParams = {
	path: {
		scene_name: string;
		game_id: number;
	};
};

export function GetParams(): RouteParams {
	return {
		path: {
			scene_name: page.params['scene_name'] as string,
			game_id: Number(page.params['game_id'])
		}
	};
}

export async function GetTerrainData(): Promise<TerrainModel[]> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/terrain', {
		params: GetParams()
	});
	if (error) throw new Error(JSON.stringify(error));

	return data;
}

export async function UpdateTerrainData(terrain: TerrainModel) {
	const { data, error } = await client.PUT('/api/{scene_name}/{game_id}/terrain', {
		params: GetParams(),
		body: terrain
	});
	if (error) throw new Error(JSON.stringify(error));
}

export async function GetUnitStatesData(): Promise<CombatUnitsViewState> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/units', {
		params: GetParams()
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

export async function performMoveActionAsync(
	unit_id: number,
	to: Vec2
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/move', {
		params: GetParams(),
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
		params: GetParams(),
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
		params: GetParams(),
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
		params: GetParams()
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}
