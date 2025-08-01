<script lang="ts">
	import type { TerrainFeatureData } from '$lib';
	import { GetClosedPath, GetSmoothedClosedPath, GetSmoothedPath } from '$lib/map/map-utils';

	type Props = {
		terrainData: TerrainFeatureData[];
	};
	let props: Props = $props();
</script>

<svg>
	<!-- Draw each polygons -->
	{#each props.terrainData as terrain}
		{#if terrain.terrainType == 'FOREST'}
			<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="forest" />
		{:else if terrain.terrainType == 'FIELD'}
			<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="field" />
		{:else if terrain.terrainType == 'WATER'}
			<path d={GetSmoothedClosedPath(terrain.coordinates, 0.7)} class="water" />
		{:else if terrain.terrainType == 'ROAD'}
			<path d={GetSmoothedPath(terrain.coordinates, 0.7)} class="road" />
		{:else if terrain.terrainType == 'BUILDING'}
			<path d={GetClosedPath(terrain.coordinates)} class="building" />
		{/if}
	{/each}
</svg>

<style lang="less">
	@stroke-width: 1.5;
	@road-width: 5;

	.road {
		fill: none;
		stroke: #d0dcb8;
		stroke-width: @road-width;
	}
	.forest {
		fill: #c1da91;
		stroke: #c1da91;
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
