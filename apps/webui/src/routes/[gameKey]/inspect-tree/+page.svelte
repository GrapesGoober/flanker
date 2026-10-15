<script lang="ts">
	import { page } from '$app/state';
	import { GetGameTreeInspection } from '$lib/api';
	import { getTreeNames, loadGameLocal, saveTreeLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let treeNames: string[] = $state([]);
	let newTreeName = $state('');
	let generating = $state(false);

	const gameKey = $derived(page.params['gameKey'] as string);

	onMount(() => {
		treeNames = getTreeNames(gameKey);
	});

	async function generateTree() {
		const treeName = newTreeName.trim();
		if (treeName.length === 0) {
			alert('Tree name is required');
			return;
		}
		if (treeNames.includes(treeName)) {
			alert('A tree with this name already exists');
			return;
		}

		generating = true;
		const gameStateJson = loadGameLocal(gameKey);
		if (!gameStateJson) {
			throw new Error(`No locally saved game state found for "${gameKey}".`);
		}

		const inspection = await GetGameTreeInspection(gameStateJson);
		if (inspection !== null) {
			saveTreeLocal(gameKey, treeName, JSON.stringify(inspection));
			treeNames = getTreeNames(gameKey);
			newTreeName = '';
		}
		generating = false;
	}
</script>

<svelte:head>
	<title>Game trees</title>
</svelte:head>

<h1>Game trees</h1>

{#if treeNames.length === 0}
	<p>No saved trees for this game.</p>
{:else}
	<ul>
		{#each treeNames as treeName}
			<li>
				<a href="/{encodeURIComponent(gameKey)}/inspect-tree/{encodeURIComponent(treeName)}">
					{treeName}
				</a>
			</li>
		{/each}
	</ul>
{/if}

<details>
	<summary>Generate a new tree</summary>
	<div>
		<input
			type="text"
			placeholder="Tree name"
			bind:value={newTreeName}
			disabled={generating}
		/>
		<input
			type="button"
			value={generating ? 'Generating…' : 'Generate tree'}
			onclick={generateTree}
			disabled={generating}
		/>
	</div>
</details>
