const prefix = 'game:';

export type QuickAccess = {
	quickAccessName: string;
	sceneNames: string[];
};

const QUICK_ACCESS_KEY = 'QUICK_ACCESSES';

export function getQuickAccesses(): QuickAccess[] {
	const quickAccesses = localStorage.getItem(QUICK_ACCESS_KEY);
	if (quickAccesses === null) return [];
	return JSON.parse(quickAccesses) as QuickAccess[];
}

export function setQuickAccesses(quick_accesses: QuickAccess[]) {
	localStorage.setItem(QUICK_ACCESS_KEY, JSON.stringify(quick_accesses));
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
