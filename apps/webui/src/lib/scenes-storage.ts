import { del, get, keys, set } from 'idb-keyval';
import type { GameTreeInspectionModel } from './api';

const prefix = 'game:';
const treePrefix = 'tree:';

export type QuickAccess = {
	quickAccessName: string;
	sceneNames: string[];
};

const QUICK_ACCESS_KEY = 'QUICK_ACCESSES';

export async function getQuickAccesses(): Promise<QuickAccess[]> {
	const quickAccesses = (await get(QUICK_ACCESS_KEY)) as QuickAccess[];
	if (quickAccesses === undefined) return [];
	return quickAccesses;
}

export async function setQuickAccesses(quickAccesses: QuickAccess[]) {
	// The given object might not me save-able, such as a proxy object.
	// This JSON parse-unparse makes sure it's a save-able object.
	const safeQuickAccesses = JSON.parse(JSON.stringify(quickAccesses));
	await set(QUICK_ACCESS_KEY, safeQuickAccesses);
}

export async function getGameKeys(): Promise<string[]> {
	return (await keys())
		.filter(
			(key): key is string => typeof key === 'string' && key.startsWith(prefix)
		)
		.map((key) => key.slice(prefix.length));
}

export async function loadGameLocal(gameKey: string): Promise<string> {
	return ((await get(prefix + gameKey)) as string) ?? '';
}

export async function deleteGameLocal(gameKey: string) {
	await del(prefix + gameKey);
}

export async function saveGameLocal(gameKey: string, jsonState: string) {
	await set(prefix + gameKey, jsonState);
}

export function getTreeNames(gameKey: string): string[] {
	const keyPrefix = `${treePrefix}${gameKey}:`;
	const names: string[] = [];
	for (let i = 0; i < localStorage.length; i++) {
		const key = localStorage.key(i);
		if (key === null || !key.startsWith(keyPrefix)) continue;
		names.push(key.slice(keyPrefix.length));
	}
	return names;
}

export function loadTreeLocal(
	gameKey: string,
	treeName: string
): GameTreeInspectionModel {
	const tree_json =
		localStorage.getItem(`${treePrefix}${gameKey}:${treeName}`) ?? '';
	if (tree_json === '') {
		throw Error('Tree ' + treeName + ' does not exist!');
	}
	return JSON.parse(tree_json) as GameTreeInspectionModel;
}

export function saveTreeLocal(
	gameKey: string,
	treeName: string,
	gameTree: GameTreeInspectionModel
) {
	localStorage.setItem(
		`${treePrefix}${gameKey}:${treeName}`,
		JSON.stringify(gameTree)
	);
}

export function deleteTreeLocal(gameKey: string, treeName: string): void {
	localStorage.removeItem(`${treePrefix}${gameKey}:${treeName}`);
}
