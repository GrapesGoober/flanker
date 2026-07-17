<script lang="ts">
	import { GetGameStateJSON } from '$lib/api';
	import { getGameKeys, loadGameLocal, saveGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let stateJson = $state('');
	let gameKey = $state('');
	let keys: string[] = $state([]);

	onMount(() => {
		keys = getGameKeys();
	});

	function loadLocal() {
		stateJson = loadGameLocal(gameKey);
	}

	async function GetGameState() {
		stateJson = await GetGameStateJSON([gameKey]);
		saveGameLocal(gameKey, stateJson);
	}
</script>

<h1>Project Flanker</h1>

Scene Name:<input bind:value={gameKey} />
<br /><br />

{keys}

<br /><br />

<button onclick={GetGameState}>Download</button>
<button onclick={loadLocal}>Load Local</button>

<br /><br />
