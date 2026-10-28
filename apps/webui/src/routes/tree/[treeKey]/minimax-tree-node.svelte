<script lang="ts">
	import type { MapViewStateModel, MinimaxTreeNodeModel } from '$lib/api';
	import { RifleSquad, SvgMap, TerrainLayer } from '$lib/components';
	import MinimaxTreeNode from './minimax-tree-node.svelte';

	type Props = {
		node: MinimaxTreeNodeModel;
		mapData: MapViewStateModel;
	};

	let { node, mapData }: Props = $props();
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

<ul>
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
						{#each node.children as edge, childIndex}
							<li>
								<details>
									<summary>{childIndex} (score: {edge.bestScore})</summary>
									<span>Action</span>
									<pre>{JSON.stringify(edge.action, null, 2)}</pre>
									<span>Node</span>
									<MinimaxTreeNode node={edge.node} {mapData} />
								</details>
							</li>
						{/each}
					</ul>
				{/if}
			</details>
		{:else}
			<p>No Children (Leaf node)</p>
		{/if}
	</li>
</ul>
