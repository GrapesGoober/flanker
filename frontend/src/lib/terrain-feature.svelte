<script lang="ts">
	import type { TerrainFeatureData } from '$lib';
	let { featureData }: { featureData: TerrainFeatureData } = $props();

	function ToString(coords: { x: number; y: number }[]): string {
		return coords.map((point) => `${point.x},${point.y}`).join(' ');
	}
</script>

{#if featureData.terrainType == 'FOREST'}
	<polygon points={ToString(featureData.coordinates)} class="forest" />
{:else if featureData.terrainType == 'ROAD'}
	<polyline points={ToString(featureData.coordinates)} class="road-border" />
	<polyline points={ToString(featureData.coordinates)} class="road" />
{:else if featureData.terrainType == 'FIELD'}
	<polygon points={ToString(featureData.coordinates)} class="field" />
{:else if featureData.terrainType == 'WATER'}
	<polygon points={ToString(featureData.coordinates)} class="water" />
{:else if featureData.terrainType == 'BUILDING'}
	<polygon points={ToString(featureData.coordinates)} class="building" />
{:else}
	<polygon points={ToString(featureData.coordinates)} fill="pink" stroke="red" stroke-width="2" />
{/if}

<style lang="less">
	@stroke-width: 1.5;
	@road-width: 5;
	.forest {
		fill: #a2bf69;
		stroke: #a2bf69;
		stroke-width: @stroke-width;
	}
	.road {
		fill: none;
		stroke: #eff6e0;
		stroke-width: @road-width;
	}
	.road-border {
		fill: none;
		stroke: #d0dcb8;
		stroke-width: @road-width + @stroke-width * 2;
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
	}
</style>
