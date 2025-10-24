<script lang="ts">
	/**
	 * Svelte layer for rendering and selecting terrain polygons in the editor.
	 * Handles terrain selection, transformation, and SVG path rendering.
	 * The terrains are drawn transparently, as it handles clicking.
	 */
	import type { TerrainModel } from '$lib/api';
	import { transform } from '$lib/map-utils';
	import { GetClosedPath, GetSmoothedClosedPath, GetSmoothedPath } from '$lib/map-utils';
	import type { EditorController } from './editor-controller.svelte';

	type Props = {
		controller: EditorController;
	};
	let props: Props = $props();

	/** Selects the given terrain in the editor controller. */
	function selectTerrain(terrain: TerrainModel) {
		props.controller.selectTerrain(terrain);
	}

	/** Returns true if the terrain is currently selected. */
	function isSelected(terrain: TerrainModel) {
		if (props.controller.state.type === 'selected') {
			return props.controller.state.terrain === terrain;
		}
		return false;
	}
</script>

<svg overflow="visible">
	<!-- Draw each polygons -->
	{#each props.controller.terrainData as terrain}
		{@const selectedClass = isSelected(terrain) ? 'selected-terrain' : ''}
		{@const vertices = transform(terrain.vertices, terrain.position, terrain.degrees)}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<g onclick={() => selectTerrain(terrain)}>
			{#if ['FOREST', 'FIELD', 'WATER'].includes(terrain.terrainType)}
				<path d={GetSmoothedClosedPath(vertices, 0.7)} class="closed-terrain {selectedClass}" />
			{:else if terrain.terrainType == 'ROAD'}
				<path d={GetSmoothedPath(vertices, 0.7)} class="open-terrain {selectedClass}" />
			{:else if terrain.terrainType == 'BUILDING'}
				<path d={GetClosedPath(vertices)} class="closed-terrain {selectedClass}" />
			{/if}
		</g>
	{/each}
</svg>

<!-- CSS being important to detect mouse clicks -->
<style lang="less">
	@road-width: 5;
	.selected-terrain {
		stroke: red !important;
	}
	.closed-terrain {
		fill: transparent;
	}
	.open-terrain {
		fill: none;
		stroke: transparent;
		stroke-width: @road-width;
	}
</style>
