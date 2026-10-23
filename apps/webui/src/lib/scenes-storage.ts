import { del, get, keys, set } from 'idb-keyval';
import type { GameTreeInspectionModel, MapViewStateModel } from './api';

const GAME_KEY_PREFIX = 'game:';
const GAME_TREE_PREFIX = 'tree:';
const QUICK_ACCESS_KEY = 'QUICK_ACCESSES';

export type QuickAccess = {
	quickAccessName: string;
	sceneNames: string[];
};

export type TreeInspectionSave = {
	mapData: MapViewStateModel;
	gameTree: GameTreeInspectionModel;
};

export async function getQuickAccesses(): Promise<QuickAccess[]> {
	const quickAccesses = (await get(QUICK_ACCESS_KEY)) as QuickAccess[];
	if (quickAccesses === undefined) return [];
	return quickAccesses;
}

export async function setQuickAccesses(quickAccesses: QuickAccess[]) {
	// Use JSON parse-unparse to strip of proxy to make it POJO save-able.
	const safeQuickAccesses = JSON.parse(JSON.stringify(quickAccesses));
	await set(QUICK_ACCESS_KEY, safeQuickAccesses);
}

export async function getGameKeys(): Promise<string[]> {
	return (await keys())
		.filter(
			(key): key is string =>
				typeof key === 'string' && key.startsWith(GAME_KEY_PREFIX)
		)
		.map((key) => key.slice(GAME_KEY_PREFIX.length));
}

export async function loadGameLocal(gameKey: string): Promise<string> {
	return ((await get(GAME_KEY_PREFIX + gameKey)) as string) ?? '';
}

export async function deleteGameLocal(gameKey: string) {
	await del(GAME_KEY_PREFIX + gameKey);
}

export async function saveGameLocal(gameKey: string, jsonState: string) {
	await set(GAME_KEY_PREFIX + gameKey, jsonState);
}

export async function getTreeKeys(): Promise<string[]> {
	return (await keys())
		.filter(
			(key): key is string =>
				typeof key === 'string' && key.startsWith(GAME_TREE_PREFIX)
		)
		.map((key) => key.slice(GAME_TREE_PREFIX.length));
}

export async function loadTreeLocal(
	treeKey: string
): Promise<TreeInspectionSave> {
	const gameTree = (await get(
		`${GAME_TREE_PREFIX}${treeKey}`
	)) as TreeInspectionSave;

	if (gameTree === undefined) {
		throw Error('Tree ' + treeKey + ' does not exist!');
	}
	return gameTree;
}

export async function saveTreeLocal(
	treeKey: string,
	gameTree: TreeInspectionSave
) {
	await set(
		`${GAME_TREE_PREFIX}${treeKey}`,
		// Use JSON parse-unparse to strip of proxy to make it POJO save-able.
		JSON.parse(JSON.stringify(gameTree))
	);
}

export async function deleteTreeLocal(treeName: string) {
	await del(`${GAME_TREE_PREFIX}${treeName}`);
}
