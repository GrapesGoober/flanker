<script lang="ts">
	import type {
		ActionRequest,
		MapViewState,
		MctsGameTreeInspectionNode
	} from '$lib/api';
	import {
		FireEffectArrows,
		RifleSquad,
		SvgMap,
		TerrainLayer
	} from '$lib/components';
	import MctsTreeNode from './mcts-tree-node.svelte';

	type Props = {
		node: MctsGameTreeInspectionNode;
		action: ActionRequest | null;
		mapData: MapViewState;
	};

	let { node, action, mapData }: Props = $props();
	let isMapOpened = $state(false);
	let areChildrenOpened = $state(false);
</script>

{#snippet mapContent()}
	<TerrainLayer {mapData} />

	<g class="transparent-map-layer">
		{#each node.viewState.fireEffectPairs as fireEffect}
			<FireEffectArrows
				positionA={fireEffect.positionA}
				positionB={fireEffect.positionB}
				fireEffectA={fireEffect.fireEffectA}
				fireEffectB={fireEffect.fireEffectB}
			/>
		{/each}
	</g>

	<svg overflow="visible">
		{#each node.viewState.squads as squad}
			<RifleSquad rifleSquadData={squad} />
		{/each}
	</svg>
{/snippet}

<ul>
	{#if action}
		<li>
			<details>
				<summary>Action</summary>
				<pre><code>{JSON.stringify(action, null, 2)}</code></pre>
			</details>
		</li>
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
						{#each node.children as edge, childIndex}
							<li>
								<details>
									<summary>{childIndex}</summary>
									<MctsTreeNode
										node={edge.node}
										action={edge.action}
										{mapData}
									/>
								</details>
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

<style lang="less">
	.transparent-map-layer {
		opacity: 0.5;
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
</style>
