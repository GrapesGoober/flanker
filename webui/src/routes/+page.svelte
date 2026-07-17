<script lang="ts">
	import { GetGameStateJSON, GetSceneNames } from '$lib/api';
	import { deleteGameLocal, getGameKeys, saveGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let saveGameKeys: string[] = $state([]);
	let sceneNames: string[] = $state([]);
	let selectedScenes: string[] = $state([]);
	let newGameName: string = $state('');

	onMount(reloadList);

	$effect(() => {
		newGameName = selectedScenes.join('-');
	});

	async function reloadList() {
		saveGameKeys = getGameKeys();
		sceneNames = await GetSceneNames();
	}

	async function createNewGame() {
		console.log(selectedScenes);
		console.log(newGameName);
		if (selectedScenes.length == 0) return;
		const stateJson = await GetGameStateJSON(selectedScenes);
		saveGameLocal(newGameName, stateJson);
		reloadList();
	}

	function deleteGameSave(gameKey: string) {
		if (confirm(`Confirm delete ${gameKey}?`)) {
			deleteGameLocal(gameKey);
			reloadList();
		}
	}
</script>

<h1>Project Flanker</h1>

<h3>Local Game Saves</h3>
{#if saveGameKeys.length === 0}
	<p>No game saves found.</p>
{:else}
	<ul>
		{#each saveGameKeys as gameKey}
			<li>
				<a href="/{gameKey}/game" class="key-link">
					<span class="key-text">{gameKey}</span>
				</a>
				<input
					type="button"
					value="❌"
					onclick={() => {
						deleteGameSave(gameKey);
					}}
				/>
			</li>
		{/each}
	</ul>
{/if}

<h3>Load Scene Presets</h3>
{#if sceneNames.length === 0}
	<p>No scene presets.</p>
{:else}
	<ul>
		{#each sceneNames as sceneName}
			<li>
				<input type="checkbox" value={sceneName} bind:group={selectedScenes} />
				{sceneName}
			</li>
		{/each}
	</ul>
{/if}

<input type="text" bind:value={newGameName} />
<input type="button" value="New Game" onclick={createNewGame} />
