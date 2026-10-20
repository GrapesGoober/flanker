import {
	GetAiMatchResult,
	GetGameStateJSON,
	GetSceneManifest,
	type SceneManifest
} from '$lib/api';
import {
	deleteGameLocal,
	getGameKeys,
	getQuickAccesses,
	loadGameLocal,
	saveGameLocal,
	setQuickAccesses,
	type QuickAccess
} from '$lib/scenes-storage';

type GameSavesControllerState = { type: 'default' } | { type: 'fetching' };

export class GameSavesController {
	state: GameSavesControllerState = $state({ type: 'default' });

	saveGameKeys: string[] = $state([]);
	sceneManifest: SceneManifest = $state({
		sceneNames: []
	});
	quickAccesses: QuickAccess[] = $state([]);

	async reloadList() {
		this.saveGameKeys = getGameKeys();
		this.sceneManifest = await GetSceneManifest();
		this.quickAccesses = getQuickAccesses();
	}

	async createNewGame(selectedScenes: string[], newGameName: string) {
		if (selectedScenes.length == 0) return;
		const stateJson = await GetGameStateJSON(selectedScenes);
		saveGameLocal(newGameName, stateJson);
		this.reloadList();
	}

	deleteGameSave(gameKey: string) {
		deleteGameLocal(gameKey);
		this.reloadList();
	}

	async createNewFromQuickAccess(quickAccess: QuickAccess) {
		const stateJson = await GetGameStateJSON(quickAccess.sceneNames);
		saveGameLocal(quickAccess.quickAccessName, stateJson);
		this.reloadList();
	}

	addQuickAccess(
		newQuickAccessName: string,
		newQuickAccessSceneNames: string[]
	) {
		const quickAccessName = newQuickAccessName.trim();

		// Create a copy to not mess with binding mutations
		const sceneNamesForQuickAccess = newQuickAccessSceneNames.slice();

		if (
			this.quickAccesses.some(
				(access) => access.quickAccessName === quickAccessName
			)
		) {
			alert('A quick access with this name already exists');
			return;
		}

		const newQuickAccess: QuickAccess = {
			quickAccessName,
			sceneNames: sceneNamesForQuickAccess
		};
		this.quickAccesses = [...this.quickAccesses, newQuickAccess];
		setQuickAccesses(this.quickAccesses);
	}

	deleteQuickAccess(quickAccessName: string) {
		this.quickAccesses = this.quickAccesses.filter(
			(access) => access.quickAccessName !== quickAccessName
		);
		setQuickAccesses(this.quickAccesses);
	}

	renameGameSave(gameKey: string, newGameKey: string) {
		if (getGameKeys().includes(newGameKey)) {
			throw Error('A save with this name already exists');
		}

		const gameStateJson = loadGameLocal(gameKey);
		deleteGameLocal(gameKey);
		saveGameLocal(newGameKey, gameStateJson);
		this.reloadList();
	}

	private generateNewGameKeyCopy(gameKey: string) {
		// It needs to automatically find a new name without deconflicts.
		// The naming scheme is to replace "xxx-copy-N" with a new number.
		const baseGameKey = gameKey.replace(/-copy-\d+$/, '');

		// Start search from the current name to find a new copy name.
		const numberMatch = gameKey.match(/-copy-(\d+)$/);
		let currentNumber = numberMatch ? Number(numberMatch[1]) : 0;
		let newGameKey = gameKey;
		while (getGameKeys().includes(newGameKey)) {
			currentNumber++;
			newGameKey = `${baseGameKey}-copy-${currentNumber}`;
		}

		return newGameKey;
	}

	duplicateGameSave(gameKey: string) {
		const newGameKey = this.generateNewGameKeyCopy(gameKey);
		saveGameLocal(newGameKey, loadGameLocal(gameKey));
		this.reloadList();
	}

	async createAiMatchSave(gameKey: string) {
		const result = await GetAiMatchResult(loadGameLocal(gameKey));
		const newGameKey = this.generateNewGameKeyCopy(gameKey);
		saveGameLocal(newGameKey, result.jsonState);
		this.reloadList();
	}

	async copyGameSaveJson(gameKey: string) {
		await navigator.clipboard.writeText(loadGameLocal(gameKey));
	}

	async copyGameSaveJsonEscaped(gameKey: string) {
		await navigator.clipboard.writeText(JSON.stringify(loadGameLocal(gameKey)));
	}
}
