export function getGameKey(sceneName: string, gameId: number) {
	return `game:${sceneName}:${gameId}`;
}

export function loadGameLocal(sceneName: string, gameId: number): string {
	return localStorage.getItem(getGameKey(sceneName, gameId)) ?? '';
}

export function saveGameLocal(sceneName: string, gameId: number, game: string) {
	localStorage.setItem(getGameKey(sceneName, gameId), game);
}
