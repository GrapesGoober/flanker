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
	<polyline points={ToString(featureData.coordinates)} class="road-border" />
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
	@road-width: 10;
	.forest {
		fill: #a2bf69;
		stroke: #a2bf69;
		stroke-width: @stroke-width;
	}
	.road {
		fill: none;
		stroke: #edcc9e;
		stroke-width: @road-width;
	}
	.road-border {
		fill: none;
		stroke: #cdb497;
		stroke-width: @road-width + @stroke-width * 2;
	}
	.water {
		fill: #a5dac6;
		stroke: #a5dac6;
		stroke-width: @stroke-width;
	}
	.field {
		fill: #f5c887;
		stroke: #cba57a;
		stroke-width: @stroke-width;
	}
</style>
