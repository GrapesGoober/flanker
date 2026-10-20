import { GetSceneManifest, type SceneManifest } from '$lib/api';
import {
	getGameKeys,
	getQuickAccesses,
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
}
