<script lang="ts">
	import { page } from '$app/state';
	import type { MctsGameTreeInspection, MctsGameTreeInspectionNode } from '$lib/api';
	import { loadTreeLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let inspection: MctsGameTreeInspection | null = $state(null);

	onMount(() => {
		const gameKey = page.params['gameKey'] as string;
		const treeKey = page.params['treeKey'] as string;
		inspection = JSON.parse(loadTreeLocal(gameKey, treeKey)) as MctsGameTreeInspection;
	});
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
	<title>Game tree</title>
</svelte:head>

<h1>Game tree</h1>

{#if inspection}
	<p>Best action: {JSON.stringify(inspection.bestAction)}</p>
	{@render treeNode(inspection.treeRoot, 'Root')}
{/if}