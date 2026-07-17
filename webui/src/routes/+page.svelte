<script lang="ts">
	import { GetGameStateJSON, GetSceneNames } from '$lib/api';
	import { getGameKeys, saveGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let gameKey = $state('');
	let saveGameKeys: string[] = $state([]);
	let sceneNames: string[] = $state([]);

	onMount(async () => {
		saveGameKeys = getGameKeys();
		sceneNames = await GetSceneNames();
	});

	async function GetGameState() {
		const stateJson = await GetGameStateJSON([gameKey]);
		saveGameLocal(gameKey, stateJson);
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
				<!-- Standard SvelteKit client-side routing anchor tag -->
				<a href="/{gameKey}/game" class="key-link">
					<span class="key-text">{gameKey}</span>
				</a>
			</li>
		{/each}
	</ul>
{/if}

<h3>Scene Presets</h3>
{#if sceneNames.length === 0}
	<p>No scene presets.</p>
{:else}
	<ul>
		{#each sceneNames as sceneName}
			<li>{sceneName}</li>
		{/each}
	</ul>
{/if}
