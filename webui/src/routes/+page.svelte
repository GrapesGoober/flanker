<script lang="ts">
	import { GetGameStateJSON } from '$lib/api';
	import { getGameKeys, saveGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let stateJson = $state('');
	let gameKey = $state('');
	let gameKeys: string[] = $state([]);

	onMount(() => {
		gameKeys = getGameKeys();
	});

	async function GetGameState() {
		stateJson = await GetGameStateJSON([gameKey]);
		saveGameLocal(gameKey, stateJson);
	}
</script>

<h1>Project Flanker</h1>

<h3>Local Game Saves</h3>
{#if gameKeys.length === 0}
	<p class="empty-state">No game saves found.</p>
{:else}
	<ul class="key-list">
		{#each gameKeys as gameKey (gameKey)}
			<li>
				<!-- Standard SvelteKit client-side routing anchor tag -->
				<a href="/{gameKey}/game" class="key-link">
					<span class="key-text">{gameKey}</span>
				</a>
			</li>
		{/each}
	</ul>
{/if}
