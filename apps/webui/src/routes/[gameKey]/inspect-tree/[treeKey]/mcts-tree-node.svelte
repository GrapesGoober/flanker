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
	import TreeNode from './mcts-tree-node.svelte';

	type Props = {
		node: MctsGameTreeInspectionNode;
		action: ActionRequest | null;
		mapData: MapViewState;
		index?: number;
	};

	let { node, action, mapData, index }: Props = $props();
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

{#snippet nodeContent()}
	<ul>
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
									<TreeNode
										node={edge.node}
										action={edge.action}
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
	<details>
		<summary>Node</summary>
		{@render nodeContent()}
	</details>
{:else}
	<details>
		<summary>{index}</summary>
		{#if action}
			<details>
				<summary>Action</summary>
				<pre><code>{JSON.stringify(action, null, 2)}</code></pre>
			</details>
		{/if}
		<details>
			<summary>Node</summary>
			{@render nodeContent()}
		</details>
	</details>
{/if}

<style lang="less">
	.transparent-map-layer {
		opacity: 0.5;
		font-size: large;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
</style>
