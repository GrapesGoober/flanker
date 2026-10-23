import { get, set } from 'idb-keyval';
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

export function getGameKeys(): string[] {
	const keys: string[] = [];
	for (let i = 0; i < localStorage.length; i++) {
		const key = localStorage.key(i);
		if (key === null) continue;
		if (!key.startsWith(prefix)) continue;
		keys.push(key.slice(prefix.length));
	}
	return keys;
}

export function loadGameLocal(gameKey: string): string {
	return localStorage.getItem(prefix + gameKey) ?? '';
}

export function deleteGameLocal(gameKey: string): string {
	return localStorage.removeItem(prefix + gameKey) ?? '';
}

export function saveGameLocal(gameKey: string, jsonState: string) {
	localStorage.setItem(prefix + gameKey, jsonState);
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
