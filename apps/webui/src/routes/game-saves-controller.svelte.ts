import {
	GetGameStateJSON,
	GetSceneManifest,
	type SceneManifest
} from '$lib/api';
import {
	deleteGameLocal,
	getGameKeys,
	getQuickAccesses,
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

	deleteQuickAccess(quickAccessName: string) {
		this.quickAccesses = this.quickAccesses.filter(
			(access) => access.quickAccessName !== quickAccessName
		);
		setQuickAccesses(this.quickAccesses);
	}
}
