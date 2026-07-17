import { page } from '$app/state';
import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';

const client = createClient<paths>({
	baseUrl: import.meta.env.VITE_WEBAPI_URL
});

export type Vec2 = components['schemas']['Vec2'];

export type TerrainModel = components['schemas']['TerrainModel'];
export type TerrainType = components['schemas']['Types'];
export type AiWaypointsModel = components['schemas']['AiWaypointConfigRequest'];
export type GameViewState = components['schemas']['GameViewState'];
export type GameViewStateResponse = components['schemas']['GameViewStateResponse'];
export type RifleSquadData = components['schemas']['SquadModel'];

export type MoveActionLog = components['schemas']['MoveActionLog'];
export type FireActionLog = components['schemas']['FireActionLog'];
export type AssaultActionLog = components['schemas']['AssaultActionLog'];
export type PivotActionLog = components['schemas']['PivotActionLog'];
export type ActionLog = MoveActionLog | FireActionLog | AssaultActionLog | PivotActionLog;

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
			sceneName: page.params['sceneName'] as string,
			gameId: Number(page.params['gameId'])
		}
	};
}

/** Get game state entities table from scene presets, in JSON string. */
export async function GetGameStateJSON(sceneNames: string[]): Promise<string> {
	const { data, error } = await client.GET('/api/json', {
		params: {
			query: {
				sceneNames: sceneNames
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));

	return data;
}

/** Get terrain data for the current game. */
export async function GetTerrainData(jsonState: string): Promise<TerrainModel[]> {
	const { data, error } = await client.POST('/api/terrain', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));

	return data;
}

/** Update terrain data for the current game. */
export async function UpdateTerrainData(
	jsonState: string,
	terrain: TerrainModel
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/terrain/update', {
		body: {
			state: jsonState,
			terrain: terrain
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Add terrain data for the current game. */
export async function AddTerrainData(
	jsonState: string,
	terrain: TerrainModel
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/terrain/add', {
		body: {
			state: jsonState,
			terrain: terrain
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Delete terrain data for the current game. */
export async function DeleteTerrainData(
	jsonState: string,
	terrainId: string
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/terrain/delete', {
		params: {
			query: {
				terrainId: terrainId
			}
		},
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get current combat unit states for the game. */
export async function GetUnitStatesData(jsonState: string): Promise<GameViewState> {
	const { data, error } = await client.POST('/api/units', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Move a unit to a target position. */
export async function performMoveActionAsync(
	jsonState: string,
	unitId: string,
	to: Vec2
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/move', {
		body: {
			state: jsonState,
			action: {
				unitId: unitId,
				to: to
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Pivots a unit towards a target position. */
export async function performPivotActionAsync(
	jsonState: string,
	unitId: string,
	to: Vec2
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/pivot', {
		body: {
			state: jsonState,
			action: {
				unitId: unitId,
				to: to
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Fire from one unit to a target unit. */
export async function performFireActionAsync(
	jsonState: string,
	unitId: string,
	targetId: string
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/fire', {
		body: {
			state: jsonState,
			action: {
				unitId: unitId,
				targetId: targetId
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Assault a target unit with a unit. */
export async function performAssaultActionAsync(
	jsonState: string,
	unitId: string,
	targetId: string
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/assault', {
		body: {
			state: jsonState,
			action: {
				unitId: unitId,
				targetId: targetId
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get action logs for the current game. */
export async function GetLogs(jsonState: string): Promise<ActionLog[]> {
	const { data, error } = await client.POST('/api/logs', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Update waypoints data for the current game. */
export async function UpdateWaypointsData(
	jsonState: string,
	waypoints: AiWaypointsModel
): Promise<GameViewStateResponse> {
	const { data, error } = await client.POST('/api/ai-config-waypoints', {
		body: {
			state: jsonState,
			configRequest: waypoints
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}
