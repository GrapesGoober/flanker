<script lang="ts">
	import type { TerrainModel } from '$lib';
	import TreeTriangle from '$lib/svg-icons/tree-triangle.svelte';
	import {
		GetClosedPath,
		GetSmoothedClosedPath,
		GetSmoothedPath,
		generatePointsInsidePolygon
	} from '$lib/map/map-utils';
	import { transform } from '$lib/linear-transform';

	type Props = {
		terrainData: TerrainModel[];
	};
	let props: Props = $props();
	// Road's boarders need to be drawn separately
	function FilterRoads(): TerrainModel[] {
		return props.terrainData.filter((feature) => feature.terrainType === 'ROAD');
	}
</script>

<g>
	<!-- Road's boarders need to be drawn separately -->
	{#each FilterRoads() as road}
		{@const vertices = transform(road.vertices, road.position, road.degrees)}
		<path d={GetSmoothedPath(vertices, 0.7)} class="road-border" />
	{/each}

	<!-- Draw each polygons -->
	{#each props.terrainData as terrain}
		{@const vertices = transform(terrain.vertices, terrain.position, terrain.degrees)}
		{#if terrain.terrainType == 'FOREST'}
			<!-- Forest has separate dashed border (so that it rests inside) -->
			<path d={GetSmoothedClosedPath(vertices, 0.7)} class="forest" />
			<path d={GetSmoothedClosedPath(vertices, 0.7)} class="forest-border" />
			{#each generatePointsInsidePolygon(vertices, 20, 15) as p}
				<g transform="translate({p.x}, {p.y})">
					<TreeTriangle />
				</g>
			{/each}
		{:else if terrain.terrainType == 'FIELD'}
			<path d={GetSmoothedClosedPath(vertices, 0.7)} class="field" />
		{:else if terrain.terrainType == 'WATER'}
			<path d={GetSmoothedClosedPath(vertices, 0.7)} class="water" />
		{:else if terrain.terrainType == 'ROAD'}
			<path d={GetSmoothedPath(vertices, 0.7)} class="road" />
		{/if}
	{/each}

	<!-- Buildings drawn on top of other polygons -->
	{#each props.terrainData as terrain}
		{@const vertices = transform(terrain.vertices, terrain.position, terrain.degrees)}
		{#if terrain.terrainType == 'BUILDING'}
			<path d={GetClosedPath(vertices)} class="building" />
		{/if}
	{/each}
</g>

<style lang="less">
	@stroke-width: 1.5;
	@road-width: 5;

	.road-border {
		fill: none;
		stroke: #d0dcb8;
		stroke-width: @road-width + @stroke-width * 2;
	}
	.road {
		fill: none;
		stroke: #eff6e0;
		stroke-width: @road-width;
	}
	.forest {
		fill: #c1da91;
		stroke: #c1da91;
		stroke-width: @stroke-width;
	}
	.forest-border {
		fill: none;
		stroke: #a2bf69;
		stroke-width: @stroke-width;
		stroke-dasharray: 8, 8;
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
