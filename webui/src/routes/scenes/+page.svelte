<script lang="ts">
	import { GetGameStateJSON, PutGameStateJSON } from '$lib/api';

	let scene = $state('');

	let sceneName = $state('');
	let gameId = $state(0);

	function storageKey(scene: string, gameId: number) {
		return `game:${scene}:${gameId}`;
	}

	function saveLocal() {
		localStorage.setItem(storageKey(sceneName, gameId), scene);
	}

	function loadLocal() {
		scene = localStorage.getItem(storageKey(sceneName, gameId)) ?? '';
	}

	function deleteLocal() {
		localStorage.removeItem(storageKey(sceneName, gameId));
	}

	async function GetGameState() {
		scene = await GetGameStateJSON(sceneName, gameId);
		saveLocal();
	}

	async function PutGameState() {
		await PutGameStateJSON(sceneName, gameId, scene);
	}
</script>

<h3>Game</h3>

Scene Name:
<input bind:value={sceneName} />

Game ID:
<input type="number" bind:value={gameId} />

<br /><br />

<button onclick={GetGameState}>Download</button>
<button onclick={PutGameState}>Upload</button>

<button onclick={saveLocal}>Save Local</button>
<button onclick={loadLocal}>Load Local</button>
<button onclick={deleteLocal}>Delete Local</button>

<br /><br />

<textarea rows="15" cols="80" bind:value={scene}></textarea>
