import {
	GetAiMatchResult,
	GetGameStateJSON,
	GetGameTreeInspection,
	GetMapData,
	GetSceneManifest,
	type SceneManifest
} from '$lib/api';
import {
	deleteGameLocal,
	deleteTreeLocal,
	getGameKeys,
	getQuickAccesses,
	getTreeKeys,
	loadGameLocal,
	saveGameLocal,
	saveTreeLocal,
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
	treeNames: string[] = $state([]);

	async reloadList() {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		this.saveGameKeys = await getGameKeys();
		this.sceneManifest = await GetSceneManifest();
		this.quickAccesses = await getQuickAccesses();
		this.treeNames = await getTreeKeys();
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

		await deleteGameLocal(gameKey);
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

	async addQuickAccess(
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
		await setQuickAccesses(this.quickAccesses);
	}

	async deleteQuickAccess(quickAccessName: string) {
		if (this.state.type === 'fetching') return;

		this.quickAccesses = this.quickAccesses.filter(
			(access) => access.quickAccessName !== quickAccessName
		);
		await setQuickAccesses(this.quickAccesses);
	}

	async renameGameSave(gameKey: string, newGameKey: string) {
		if (this.state.type === 'fetching') return;

		if ((await getGameKeys()).includes(newGameKey)) {
			throw Error('A save with this name already exists');
		}

		const gameStateJson = await loadGameLocal(gameKey);
		await deleteGameLocal(gameKey);
		await saveGameLocal(newGameKey, gameStateJson);
		await this.reloadList();
	}

	async duplicateGameSave(gameKey: string) {
		if (this.state.type === 'fetching') return;

		const newGameKey = this.getDeduplicatedKey(gameKey, await getGameKeys());
		saveGameLocal(newGameKey, await loadGameLocal(gameKey));
		await this.reloadList();
	}

	async createAiMatchSave(gameKey: string) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		const result = await GetAiMatchResult(await loadGameLocal(gameKey));
		const newGameKey = this.getDeduplicatedKey(gameKey, await getGameKeys());
		saveGameLocal(await newGameKey, result.jsonState);
		this.state = { type: 'default' };
		await this.reloadList();
	}

	async copyGameSaveJson(gameKey: string) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		await navigator.clipboard.writeText(await loadGameLocal(gameKey));
		this.state = { type: 'default' };
	}

	async copyGameSaveJsonEscaped(gameKey: string) {
		if (this.state.type === 'fetching') return;
		this.state = { type: 'fetching' };
		await navigator.clipboard.writeText(
			JSON.stringify(await loadGameLocal(gameKey))
		);
		this.state = { type: 'default' };
	}
	async createTree(gameKey: string) {
		this.state = { type: 'fetching' };

		const gameStateJson = await loadGameLocal(gameKey);
		const gameTree = await GetGameTreeInspection(gameStateJson);
		const mapData = await GetMapData(gameStateJson);
		const newTreeName = this.getDeduplicatedKey(gameKey, await getTreeKeys());
		if (gameTree !== null && mapData !== null) {
			saveTreeLocal(newTreeName, {
				mapData: mapData,
				gameTree: gameTree
			});
		}
		this.state = { type: 'default' };
		this.reloadList();
	}

	async deleteTree(treeName: string) {
		await deleteTreeLocal(treeName);
		this.reloadList();
	}

	private getDeduplicatedKey(key: string, otherKeys: string[]): string {
		// It needs to automatically find a new key deconflicts.
		// The naming scheme is to replace "xxx-copy-N" with a new number.
		const baseKey = key.replace(/-copy-\d+$/, '');

		// Start search from the current number to find an unused key.
		const numberMatch = key.match(/-copy-(\d+)$/);
		let currentNumber = numberMatch ? Number(numberMatch[1]) : 0;
		let newGameKey = key;
		while (otherKeys.includes(newGameKey)) {
			currentNumber++;
			newGameKey = `${baseKey}-copy-${currentNumber}`;
		}

		return newGameKey;
	}
}
