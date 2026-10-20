<script lang="ts">
	import type { ExpectimaxTreeNodeModel, MapViewStateModel } from '$lib/api';
	import {
		FireEffectArrows,
		RifleSquad,
		SvgMap,
		TerrainLayer
	} from '$lib/components';
	import ExpectimaxTreeNode from './expectimax-tree-node.svelte';

	type Props = {
		node: ExpectimaxTreeNodeModel;
		mapData: MapViewStateModel;
	};

	let { node, mapData }: Props = $props();
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
						{#each node.children as edge, edgeIndex}
							<li>
								<details>
									<summary>
										{edgeIndex} (expected score: {edge.expectedScore})
									</summary>
									<span>Action</span>
									<pre>{JSON.stringify(edge.action, null, 2)}</pre>
									<span>Outcomes</span>
									<ul>
										{#each edge.outcomes as outcome, outcomeIndex}
											<li>
												<details>
													<summary>
														{outcomeIndex} (probability: {outcome.probability},
														score: {outcome.score})
													</summary>
													<span>Node</span>
													<ExpectimaxTreeNode node={outcome.node} {mapData} />
												</details>
											</li>
										{/each}
									</ul>
								</details>
							</li>
						{/each}
					</ul>
				{/if}
			</details>
		{:else}
			<span>No Children (Leaf node)</span>
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
