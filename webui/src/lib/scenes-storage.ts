export function getGameKey(sceneName: string) {
	return `game:${sceneName}`;
}

export function loadGameLocal(sceneName: string): string {
	return localStorage.getItem(getGameKey(sceneName)) ?? '';
}

export function saveGameLocal(sceneName: string, game: string) {
	localStorage.setItem(getGameKey(sceneName), game);
}
