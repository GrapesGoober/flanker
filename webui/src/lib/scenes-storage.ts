const prefix = 'game:';

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
