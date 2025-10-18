import createClient from 'openapi-fetch';
import type { components, paths } from './api-schema';
const client = createClient<paths>();

export type Vec2 = { x: number; y: number };

export type TerrainFeatureData = {
	terrainId: number;
	terrainType: 'FOREST' | 'ROAD' | 'FIELD' | 'WATER' | 'BUILDING';
	position: Vec2;
	degrees: number;
	vertices: Vec2[];
};

export async function GetTerrainData(): Promise<TerrainFeatureData[]> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/terrain', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));

	// Convert to a custom type in case API and types diverge
	const terrainData: TerrainFeatureData[] = data.map((element) => ({
		terrainId: element.terrain_id,
		terrainType: element.terrain_type,
		position: element.position,
		degrees: element.degrees,
		vertices: element.vertices
	}));

	return terrainData;
}

export async function UpdateTerrainData(terrain: TerrainFeatureData) {
	const { data, error } = await client.PUT('/api/{scene_name}/{game_id}/terrain', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		},
		body: {
			terrain_id: terrain.terrainId,
			terrain_type: terrain.terrainType,
			position: terrain.position,
			degrees: terrain.degrees,
			vertices: terrain.vertices
		}
	});
	if (error) throw new Error(JSON.stringify(error));
}

export type CombatUnitsViewState = {
	objectivesState: 'INCOMPLETE' | 'COMPLETED' | 'FAILED';
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

function ParseCombatUnitsViewState(
	data: components['schemas']['CombatUnitsViewState']
): CombatUnitsViewState {
	return {
		objectivesState: data.objective_state,
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

export async function GetUnitStatesData(): Promise<CombatUnitsViewState> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/units', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return ParseCombatUnitsViewState(data);
}

export async function performMoveActionAsync(
	unit_id: number,
	to: Vec2
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/move', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		},
		body: {
			unit_id: unit_id,
			to: to
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return ParseCombatUnitsViewState(data);
}

export async function performFireActionAsync(
	unit_id: number,
	target_id: number
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/fire', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		},
		body: {
			unit_id: unit_id,
			target_id: target_id
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return ParseCombatUnitsViewState(data);
}

export async function performAssaultActionAsync(
	unit_id: number,
	target_id: number
): Promise<CombatUnitsViewState> {
	const { data, error } = await client.POST('/api/{scene_name}/{game_id}/assault', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		},
		body: {
			unit_id: unit_id,
			target_id: target_id
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	return ParseCombatUnitsViewState(data);
}

export type ActionType = 'move' | 'fire' | 'assault';

export type MoveActionRequest = {
	unitId: number;
	to: Vec2;
};

export type FireActionRequest = {
	unitId: number;
	targetId: number;
};

export type AssaultActionRequest = {
	unitId: number;
	targetId: number;
};

export enum FireOutcome {
	MISS = 'MISS',
	PIN = 'PIN',
	SUPPRESS = 'SUPPRESS',
	KILL = 'KILL'
}

export enum AssaultOutcome {
	FAIL = 'FAIL',
	SUCCESS = 'SUCCESS'
}

export type MoveActionResult = {
	fireOutcome: FireOutcome;
};

export type FireActionResult = {
	isHit: boolean;
	outcome: FireOutcome;
};

export type AssaultActionResult = {
	result: AssaultOutcome;
};

export type MoveActionLog = {
	type: 'move';
	body: MoveActionRequest;
	result: MoveActionResult;
	unitState: CombatUnitsViewState;
};

export type FireActionLog = {
	type: 'fire';
	body: FireActionRequest;
	result: FireActionResult;
	unitState: CombatUnitsViewState;
};

export type AssaultActionLog = {
	type: 'assault';
	body: AssaultActionRequest;
	result: AssaultActionResult;
	unitState: CombatUnitsViewState;
};

export type ActionLog = MoveActionLog | FireActionLog | AssaultActionLog;

export async function GetLogs(): Promise<ActionLog[]> {
	const { data, error } = await client.GET('/api/{scene_name}/{game_id}/logs', {
		params: {
			path: {
				scene_name: 'demo',
				game_id: 0
			}
		}
	});
	if (error) throw new Error(JSON.stringify(error));
	// Map each log entry to the correct ActionLog type and parse unitState
	return data.map(
		(
			log:
				| components['schemas']['MoveActionLog']
				| components['schemas']['FireActionLog']
				| components['schemas']['AssaultActionLog']
		) => {
			console.log(log);
			const unitState = ParseCombatUnitsViewState(log.unit_state);
			if (log.type === 'move' && 'to' in log.body && 'reactive_fire_outcome' in log.result) {
				return {
					type: 'move',
					body: {
						unitId: log.body.unit_id,
						to: log.body.to
					},
					result: {
						fireOutcome: log.result.reactive_fire_outcome
					},
					unitState
				} as MoveActionLog;
			} else if (log.type === 'fire' && 'target_id' in log.body && 'outcome' in log.result) {
				return {
					type: 'fire',
					body: {
						unitId: log.body.unit_id,
						targetId: log.body.target_id
					},
					result: {
						outcome: (log.result.outcome ?? null) as FireOutcome
					},
					unitState
				} as FireActionLog;
			} else if (log.type === 'assault' && 'target_id' in log.body && 'outcome' in log.result) {
				return {
					type: 'assault',
					body: {
						unitId: log.body.unit_id,
						targetId: log.body.target_id
					},
					result: {
						result: log.result.outcome
					},
					unitState
				} as AssaultActionLog;
			} else {
				throw new Error('Unknown log type or malformed log body/result');
			}
		}
	);
}
