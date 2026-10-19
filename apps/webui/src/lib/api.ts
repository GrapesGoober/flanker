import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';

const client = createClient<paths>({
	baseUrl: import.meta.env.VITE_WEBAPI_URL
});

export type SceneManifest = components['schemas']['SceneManifestResponse'];

export type Vec2 = components['schemas']['Vec2'];

export type TerrainModel = components['schemas']['TerrainModel'];
export type TerrainType = components['schemas']['TerrainType'];
export type AiWaypointsModel =
	components['schemas']['AiWaypointConfigRequestModel'];
export type GameViewStateModel = components['schemas']['GameViewStateModel'];
export type GameViewStateResponseModel =
	components['schemas']['GameViewStateResponseModel'];
export type GameStateInspectionModel =
	components['schemas']['GameStateInspectionModel'];
export type MctsTreeNodeModel = components['schemas']['MctsTreeNodeModel'];
export type MinimaxTreeNodeModel =
	components['schemas']['MinimaxTreeNodeModel'];
export type ExpectimaxTreeNodeModel =
	components['schemas']['ExpectimaxTreeNodeModel'];
export type GameTreeInspectionModel =
	components['schemas']['GameTreeInspectionModel'];
export type MapViewStateModel = components['schemas']['MapViewStateModel'];
export type RifleSquadData = components['schemas']['SquadModel'];
export type FireEffect = components['schemas']['FireEffect'];

export type MoveActionModel = components['schemas']['MoveActionModel'];
export type FireActionModel = components['schemas']['FireActionModel'];
export type AssaultActionModel = components['schemas']['AssaultActionModel'];
export type PivotActionModel = components['schemas']['PivotActionModel'];
export type ActionModel =
	| MoveActionModel
	| FireActionModel
	| AssaultActionModel
	| PivotActionModel;

export type MoveActionLogModel = components['schemas']['MoveActionLogModel'];
export type FireActionLogModel = components['schemas']['FireActionLogModel'];
export type AssaultActionLogModel =
	components['schemas']['AssaultActionLogModel'];
export type PivotActionLogModel = components['schemas']['PivotActionLogModel'];
export type ActionLogModel =
	| MoveActionLogModel
	| FireActionLogModel
	| AssaultActionLogModel
	| PivotActionLogModel;

/** Get all available scene names. */
export async function GetSceneNames(): Promise<SceneManifest> {
	const { data, error } = await client.GET('/api/scenes');
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get current combat unit states for the game. */
export async function GetViewStatesData(
	jsonState: string
): Promise<GameViewStateModel> {
	const { data, error } = await client.POST('/api/game/view', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get current combat unit states for the game. */
export async function GetStatesInspectionData(
	jsonState: string
): Promise<GameStateInspectionModel> {
	const { data, error } = await client.POST('/api/game/inspect', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get the game tree inspection for the current game. */
export async function GetGameTreeInspection(
	jsonState: string
): Promise<GameTreeInspectionModel | null> {
	const { data, error } = await client.POST('/api/game/inspect/game-tree', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get game state entities table from scene presets, in JSON string. */
export async function GetGameStateJSON(sceneNames: string[]): Promise<string> {
	const { data, error } = await client.GET('/api/scenes/json', {
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
export async function GetMapData(
	jsonState: string
): Promise<MapViewStateModel> {
	const { data, error } = await client.POST('/api/game/map', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));

	return data;
}

export async function performActionAsync(
	jsonState: string,
	action: ActionModel
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.POST('/api/game/perform', {
		body: {
			state: jsonState,
			action: action
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Get action logs for the current game. */
export async function GetLogs(jsonState: string): Promise<ActionLogModel[]> {
	const { data, error } = await client.POST('/api/game/logs', {
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Update terrain data for the current game. */
export async function UpdateTerrainData(
	jsonState: string,
	terrain: TerrainModel
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.PUT('/api/editor/terrain', {
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
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.POST('/api/editor/terrain', {
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
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.DELETE('/api/editor/terrain', {
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

/** Adds a new combat unit to the current game. */
export async function AddUnit(
	jsonState: string,
	unit: RifleSquadData
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.POST('/api/editor/unit', {
		body: {
			state: jsonState,
			unit: unit
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Updates the unit data for the current game. */
export async function UpdateUnit(
	jsonState: string,
	unit: RifleSquadData
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.PUT('/api/editor/unit', {
		body: {
			state: jsonState,
			unit: unit
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Adds a new combat unit to the current game. */
export async function DeleteUnit(
	jsonState: string,
	unitId: string
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.DELETE('/api/editor/unit', {
		params: {
			query: {
				unitId: unitId
			}
		},
		body: jsonState
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}

/** Update waypoints data for the current game. */
export async function UpdateWaypointsData(
	jsonState: string,
	waypoints: AiWaypointsModel
): Promise<GameViewStateResponseModel> {
	const { data, error } = await client.PUT('/api/editor/ai-waypoints', {
		body: {
			state: jsonState,
			configRequest: waypoints
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return data;
}
