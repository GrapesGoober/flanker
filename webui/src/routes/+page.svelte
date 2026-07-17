<script lang="ts">
	import { GetGameStateJSON } from '$lib/api';
	import { getGameKeys, loadGameLocal, saveGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let stateJson = $state('');
	let sceneName = $state('');
	let keys: string[] = $state([]);

	onMount(() => {
		keys = getGameKeys();
	});

	function loadLocal() {
		stateJson = loadGameLocal(sceneName);
	}

	async function GetGameState() {
		stateJson = await GetGameStateJSON([sceneName]);
		saveGameLocal(sceneName, stateJson);
	}
</script>

<h1>Project Flanker</h1>

Scene Name:<input bind:value={sceneName} />
<br /><br />

{keys}

<br /><br />

<button onclick={GetGameState}>Download</button>
<button onclick={loadLocal}>Load Local</button>

<br /><br />
