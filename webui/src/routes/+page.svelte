<script lang="ts">
	import { GetGameStateJSON } from '$lib/api';
	import { loadGameLocal, saveGameLocal } from '$lib/scenes-storage';

	let stateJson = $state('');

	let sceneName = $state('');

	function loadLocal() {
		stateJson = loadGameLocal(sceneName);
	}

	async function GetGameState() {
		stateJson = await GetGameStateJSON([sceneName]);
		saveGameLocal(sceneName, stateJson);
	}
</script>

<h3>Game</h3>

Scene Name:<input bind:value={sceneName} />

<br /><br />

<button onclick={GetGameState}>Download</button>
<button onclick={loadLocal}>Load Local</button>

<br /><br />

<textarea rows="15" cols="80" bind:value={stateJson}></textarea>
