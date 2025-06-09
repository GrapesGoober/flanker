<script lang="ts">
	import { TerrainType, type TerrainFeatureData } from '$lib';
	let { featureData }: { featureData: TerrainFeatureData } = $props();

	function ToString(coords: { x: number; y: number }[]): string {
		return coords.map((point) => `${point.x},${point.y}`).join(' ');
	}
</script>

{#if featureData.terrain_type == TerrainType.Forest}
	<polygon points={ToString(featureData.coordinates)} class="forest" />
{:else if featureData.terrain_type == TerrainType.Road}
	<polyline points={ToString(featureData.coordinates)} class="road" />
{:else if featureData.terrain_type == TerrainType.Field}
	<polygon points={ToString(featureData.coordinates)} class="field" />
{:else if featureData.terrain_type == TerrainType.Water}
	<polygon points={ToString(featureData.coordinates)} class="water" />
{:else}
	<polygon points={ToString(featureData.coordinates)} fill="pink" stroke="red" stroke-width="2" />
{/if}

<style lang="less">
	@stroke-width: 2;
	@road-width: 4;
	.forest {
		fill: #ccd5ae;
		stroke: #c2cca0;
		stroke-width: @stroke-width;
	}
	.road {
		fill: none;
		stroke: #d3c1b0;
		stroke-width: @road-width;
	}
	.water {
		fill: #c6e3fd;
		stroke: #a2d2ff;
		stroke-width: @stroke-width;
	}
	.field {
		fill: beige;
		stroke: burlywood;
		stroke-width: @stroke-width;
	}
</style>
