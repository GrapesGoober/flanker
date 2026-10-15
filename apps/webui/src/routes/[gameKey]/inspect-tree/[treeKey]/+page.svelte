<script lang="ts">
	import { page } from '$app/state';
	import type {
		ActionRequest,
		MctsGameTreeInspection,
		MctsGameTreeInspectionNode
	} from '$lib/api';
	import { loadTreeLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let inspection: MctsGameTreeInspection | null = $state(null);

	onMount(() => {
		const gameKey = page.params['gameKey'] as string;
		const treeKey = page.params['treeKey'] as string;
		inspection = JSON.parse(
			loadTreeLocal(gameKey, treeKey)
		) as MctsGameTreeInspection;
	});
</script>

{#snippet treeNode(node: MctsGameTreeInspectionNode, action: ActionRequest | null)}
	<div>
		<ul>
			{#if action}
				<li><pre><code>{JSON.stringify(action, null, 2)}</code></pre></li>
			{/if}
			<li>visits: {node.totalVisits}, value: {node.totalValue}</li>

			<li>
				Objective: {node.viewState.objectiveState}; initiative: {node.viewState
					.hasInitiative}; squads: {node.viewState.squads.length}
			</li>
			<li>
				<details>
					<summary>View state</summary>
					<pre>{JSON.stringify(node.viewState, null, 2)}</pre>
				</details>
			</li>

			<li>
				{#if node.children.length > 0}
					<details>
						<summary>Children ({node.children.length})</summary>
						<ul>
							{#each node.children as [action, child], index}
								<li>
									<details>
										<summary>{index}</summary>
										{@render treeNode(child, action)}
									</details>
								</li>
							{/each}
						</ul>
					</details>
				{:else}
					<p>Leaf node</p>
				{/if}
			</li>
		</ul>
	</div>
{/snippet}

<svelte:head>
	<title>Game tree</title>
</svelte:head>

<h1>Game tree</h1>

{#if inspection}
	<p>Best action</p>
	<pre><code>{JSON.stringify(inspection.bestAction, null, 2)}</code></pre>
	{@render treeNode(inspection.treeRoot, null)}
{/if}
