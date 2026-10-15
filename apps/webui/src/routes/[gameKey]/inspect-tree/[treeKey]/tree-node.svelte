<script lang="ts">
	import type {
		ActionRequest,
		MapViewState,
		MctsGameTreeInspectionNode
	} from '$lib/api';
	import { RifleSquad, SvgMap, TerrainLayer } from '$lib/components';
	import TreeNode from './tree-node.svelte';

	type Props = {
		node: MctsGameTreeInspectionNode;
		action: ActionRequest | null;
		mapData: MapViewState;
		index?: number;
	};

	let { node, action, mapData, index }: Props = $props();
	let isOpened = $state(false);
	let isMapOpened = $state(false);
	let areChildrenOpened = $state(false);
</script>

{#snippet mapContent()}
	<TerrainLayer {mapData} />
	<svg overflow="visible">
		{#each node.viewState.squads as squad}
			<RifleSquad rifleSquadData={squad} />
		{/each}
	</svg>
{/snippet}

{#snippet nodeContent()}
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
			<details bind:open={isMapOpened}>
				<summary>Map</summary>
				{#if isMapOpened}
					<SvgMap
						svgSnippet={mapContent}
						width="35vw"
						height="35vh"
						initialZoom={1}
					/>
				{/if}
			</details>
		</li>
		<li>
			{#if node.children.length > 0}
				<details bind:open={areChildrenOpened}>
					<summary>Children ({node.children.length})</summary>
					{#if areChildrenOpened}
						<ul>
							{#each node.children as [childAction, childNode], childIndex}
								<li>
									<TreeNode
										node={childNode}
										action={childAction}
										{mapData}
										index={childIndex}
									/>
								</li>
							{/each}
						</ul>
					{/if}
				</details>
			{:else}
				<p>Leaf node</p>
			{/if}
		</li>
	</ul>
{/snippet}

{#if index === undefined}
	{@render nodeContent()}
{:else}
	<details bind:open={isOpened}>
		<summary>{index}</summary>
		{#if isOpened}
			{@render nodeContent()}
		{/if}
	</details>
{/if}
