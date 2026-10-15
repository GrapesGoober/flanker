<script lang="ts">
	import { page } from '$app/state';
	import {
		GetGameTreeInspection,
		type MctsGameTreeInspectionNode
	} from '$lib/api';
	import { loadGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let treeRoot: MctsGameTreeInspectionNode | null = $state(null);
	let bestAction = $state('');
	let loading = $state(true);

	onMount(() => {
		void loadTree();
	});

	async function loadTree() {
		const gameKey = page.params['gameKey'] as string;
		const gameStateJson = loadGameLocal(gameKey);
		if (!gameStateJson) {
			throw new Error(`No locally saved game state found for "${gameKey}".`);
		}

		const inspection = await GetGameTreeInspection(gameStateJson);
		if (inspection !== null) {
			bestAction = JSON.stringify(inspection.bestAction);
			treeRoot = inspection.treeRoot;
		}
		loading = false;
	}
</script>

{#snippet treeNode(node: MctsGameTreeInspectionNode, actionLabel: string)}
	<details>
		<summary
			>{actionLabel} — visits: {node.totalVisits}, value: {node.totalValue}</summary
		>
		<p>
			Objective: {node.viewState.objectiveState}; initiative: {node.viewState
				.hasInitiative}; squads: {node.viewState.squads.length}
		</p>
		<details>
			<summary>View state</summary>
			<pre>{JSON.stringify(node.viewState, null, 2)}</pre>
		</details>
		{#if node.children.length > 0}
			<ul>
				{#each node.children as [action, child]}
					<li>{@render treeNode(child, JSON.stringify(action))}</li>
				{/each}
			</ul>
		{:else}
			<p>Leaf node</p>
		{/if}
	</details>
{/snippet}

<svelte:head>
	<title>Inspect game tree</title>
</svelte:head>

<h1>MCTS game tree</h1>

{#if loading}
	<p>Loading game tree…</p>
{:else if treeRoot}
	<p>Best action: {bestAction}</p>
	{@render treeNode(treeRoot, 'Root')}
{:else}
	<p>No MCTS tree is available for this game state.</p>
{/if}
