<script lang="ts">
	import { GetGameStateJSON } from '$lib/api';
	import { loadGameLocal } from '$lib/scenes-storage';

	let scene = $state('');

	let sceneName = $state('');

	function storageKey(scene: string) {
		return `game:${scene}`;
	}

	function loadLocal() {
		scene = loadGameLocal(sceneName);
	}

	async function GetGameState() {
		scene = await GetGameStateJSON([sceneName]);
		localStorage.setItem(storageKey(sceneName), scene);
	}
</script>

<h3>Game</h3>

Scene Name:<input bind:value={sceneName} />

<br /><br />

<button onclick={GetGameState}>Download</button>
<button onclick={loadLocal}>Load Local</button>

<br /><br />

<textarea rows="15" cols="80" bind:value={scene}></textarea>
