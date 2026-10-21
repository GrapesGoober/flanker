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
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		this.saveGameKeys = getGameKeys();
		this.sceneManifest = await GetSceneManifest();
		this.quickAccesses = getQuickAccesses();
		this.state = { type: 'default' };
	}

	async createNewGame(selectedScenes: string[], newGameName: string) {
		if (this.state.type === 'fetching' || selectedScenes.length === 0) return;
		this.state = { type: 'fetching' };
		const stateJson = await GetGameStateJSON(selectedScenes);
		saveGameLocal(newGameName, stateJson);
		this.state = { type: 'default' };
		await this.reloadList();
	}

	async deleteGameSave(gameKey: string) {
		if (this.state.type === 'fetching') return;

		deleteGameLocal(gameKey);
		await this.reloadList();
	}

	async createNewFromQuickAccess(quickAccess: QuickAccess) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		const stateJson = await GetGameStateJSON(quickAccess.sceneNames);
		saveGameLocal(quickAccess.quickAccessName, stateJson);
		this.state = { type: 'default' };
		await this.reloadList();
	}

	addQuickAccess(
		newQuickAccessName: string,
		newQuickAccessSceneNames: string[]
	) {
		if (this.state.type === 'fetching') return;

		const quickAccessName = newQuickAccessName.trim();

		// Create a copy to not mess with binding mutations
		const sceneNamesForQuickAccess = newQuickAccessSceneNames.slice();

		if (quickAccessName.length === 0) {
			throw Error('Quick access name is required');
		}
		if (newQuickAccessSceneNames.length === 0) {
			throw Error('Select at least one scene');
		}

		if (
			this.quickAccesses.some(
				(access) => access.quickAccessName === quickAccessName
			)
		) {
			throw Error('A quick access with this name already exists');
		}

		const newQuickAccess: QuickAccess = {
			quickAccessName,
			sceneNames: sceneNamesForQuickAccess
		};
		this.quickAccesses = [...this.quickAccesses, newQuickAccess];
		setQuickAccesses(this.quickAccesses);
	}

	deleteQuickAccess(quickAccessName: string) {
		if (this.state.type === 'fetching') return;

		this.quickAccesses = this.quickAccesses.filter(
			(access) => access.quickAccessName !== quickAccessName
		);
		setQuickAccesses(this.quickAccesses);
	}

	async renameGameSave(gameKey: string, newGameKey: string) {
		if (this.state.type === 'fetching') return;

		if (getGameKeys().includes(newGameKey)) {
			throw Error('A save with this name already exists');
		}

		const gameStateJson = loadGameLocal(gameKey);
		deleteGameLocal(gameKey);
		saveGameLocal(newGameKey, gameStateJson);
		await this.reloadList();
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

	async duplicateGameSave(gameKey: string) {
		if (this.state.type === 'fetching') return;

		const newGameKey = this.generateNewGameKeyCopy(gameKey);
		saveGameLocal(newGameKey, loadGameLocal(gameKey));
		await this.reloadList();
	}

	async createAiMatchSave(gameKey: string) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		const result = await GetAiMatchResult(loadGameLocal(gameKey));
		const newGameKey = this.generateNewGameKeyCopy(gameKey);
		saveGameLocal(newGameKey, result.jsonState);
		this.state = { type: 'default' };
		await this.reloadList();
	}

	async copyGameSaveJson(gameKey: string) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		await navigator.clipboard.writeText(loadGameLocal(gameKey));
		this.state = { type: 'default' };
	}

	async copyGameSaveJsonEscaped(gameKey: string) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		await navigator.clipboard.writeText(JSON.stringify(loadGameLocal(gameKey)));
		this.state = { type: 'default' };
	}
}
