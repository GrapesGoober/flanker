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
		sceneName: string;
		gameId: number;
	};
};

/** Get route parameters from the current page. */
export function GetParams(): RouteParams {
	return {
		path: {
			sceneName: page.params['scene_name'] as string,
			gameId: Number(page.params['game_id'])
		}
	};
}

/** Fetch terrain data for the current scene/game. */
export async function GetTerrainData(): Promise<TerrainModel[]> {
	const { data, error } = await client.GET('/api/{sceneName}/{gameId}/terrain', {
		params: GetParams()
	});
	if (error) throw new Error(JSON.stringify(error));

	return data;
}

/** Update terrain data for the current scene/game. */
export async function UpdateTerrainData(terrain: TerrainModel) {
	const { data, error } = await client.PUT('/api/{sceneName}/{gameId}/terrain', {
		params: GetParams(),
		body: terrain
	});
	if (error) throw new Error(JSON.stringify(error));
}

/** Get current combat unit states for the scene/game. */
export async function GetUnitStatesData(): Promise<CombatUnitsViewState> {
	const { data, error } = await client.GET('/api/{sceneName}/{gameId}/units', {
		params: GetParams()
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Move a unit to a target position. */
export async function performMoveActionAsync(
	unitId: number,
	to: Vec2
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{sceneName}/{gameId}/move', {
		params: GetParams(),
		body: {
			unitId: unitId,
			to: to
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Fire from one unit to a target unit. */
export async function performFireActionAsync(
	unitId: number,
	targetId: number
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{sceneName}/{gameId}/fire', {
		params: GetParams(),
		body: {
			unitId: unitId,
			targetId: targetId
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Assault a target unit with a unit. */
export async function performAssaultActionAsync(
	unitId: number,
	targetId: number
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{sceneName}/{gameId}/assault', {
		params: GetParams(),
		body: {
			unitId: unitId,
			targetId: targetId
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get action logs for the current scene/game. */
export async function GetLogs(): Promise<ActionLog[]> {
	const { data, error } = await client.GET('/api/{sceneName}/{gameId}/logs', {
		params: GetParams()
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}
