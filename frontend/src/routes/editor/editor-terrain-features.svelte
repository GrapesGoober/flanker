<script lang="ts">
	import type { TerrainModel } from '$lib';
	import { transform } from '$lib/linear-transform';
	import { GetClosedPath, GetSmoothedClosedPath, GetSmoothedPath } from '$lib/map/map-utils';
	import type { EditorController } from './editor-controller.svelte';

	type Props = {
		controller: EditorController;
	};
	let props: Props = $props();

	function selectTerrain(terrain: TerrainModel) {
		props.controller.selectTerrain(terrain);
	}

	function isSelected(terrain: TerrainModel) {
		if (props.controller.state.type === 'selected') {
			return props.controller.state.terrain === terrain;
		}
		return false;
	}
</script>

<g>
	<!-- Draw each polygons -->
	{#each props.controller.terrainData as terrain}
		{@const selectedClass = isSelected(terrain) ? 'selected-terrain' : ''}
		{@const vertices = transform(terrain.vertices, terrain.position, terrain.degrees)}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<g onclick={() => selectTerrain(terrain)}>
			{#if terrain.terrainType == 'FOREST'}
				<path d={GetSmoothedClosedPath(vertices, 0.7)} class="forest {selectedClass}" />
			{:else if terrain.terrainType == 'FIELD'}
				<path d={GetSmoothedClosedPath(vertices, 0.7)} class="field {selectedClass}" />
			{:else if terrain.terrainType == 'WATER'}
				<path d={GetSmoothedClosedPath(vertices, 0.7)} class="water {selectedClass}" />
			{:else if terrain.terrainType == 'ROAD'}
				<path d={GetSmoothedPath(vertices, 0.7)} class="road {selectedClass}" />
			{:else if terrain.terrainType == 'BUILDING'}
				<path d={GetClosedPath(vertices)} class="building {selectedClass}" />
			{/if}
		</g>
	{/each}
</g>

<style lang="less">
	@stroke-width: 1.5;
	@road-width: 5;

	.selected-terrain {
		stroke: red !important;
	}
	.road {
		fill: none;
		stroke: #bbc5a5;
		stroke-width: @road-width + @stroke-width * 2;
	}
	.forest {
		fill: #c1da91;
		stroke: #a2b879;
		stroke-width: @stroke-width;
	}
	.water {
		fill: #a5dac6;
		stroke: #a5dac6;
		stroke-width: @stroke-width;
	}
	.field {
		fill: #f5c887aa;
		stroke: #cba57aaa;
		stroke-width: @stroke-width;
	}
	.building {
		fill: #aaa;
		stroke: #999;
		stroke-width: @stroke-width;
		stroke-linecap: square;
	}
</style>
