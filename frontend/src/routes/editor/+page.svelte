<script lang="ts">
	import { onMount } from 'svelte';
	import { GetTerrainData, type TerrainFeatureData, type Vec2 } from '$lib';
	import TerrainFeature from '$lib/terrain-feature.svelte';
	import SvgMap from '$lib/svg-map.svelte';

	let terrainData: TerrainFeatureData[] = $state([]);
	let coords: Vec2[] = $state([]);

	onMount(async () => {
		terrainData = await GetTerrainData();
	});

	function AddMarker(event: MouseEvent, worldPos: Vec2) {
		coords.push(worldPos);
	}

	function ToString(coords: { x: number; y: number }[]): string {
		return coords.map((point) => `${point.x},${point.y}`).join(' ');
	}
	function ToPythonListString(coords: Vec2[]): string {
		return (
			'[\n' + coords.map((c) => `Vec2(${Math.round(c.x)}, ${Math.round(c.y)}),`).join('\n') + '\n]'
		);
	}

	function refreshTerrainData() {
		coords = [];
		GetTerrainData().then((data) => {
			terrainData = data;
		});
	}
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapMarkup()}
	{#each terrainData as terrainFeatureData}
		<TerrainFeature featureData={terrainFeatureData} />
	{/each}

	<polygon points={ToString(coords)} class="forest" />

	<rect x="200" y="200" width="100" height="100" fill="none" stroke="black" />
{/snippet}

<SvgMap onclick={AddMarker} body={mapMarkup} />
<button onclick={refreshTerrainData} style="margin-bottom: 1em;">Refresh</button>

<textarea
	readonly
	style="width: 100%; min-height: 120px; resize: vertical; font-family: monospace; margin-top: 1em;"
	value={ToPythonListString(coords)}
></textarea>

<style lang="less">
	@stroke-width: 1;
	.forest {
		fill: #ccd5ae;
		stroke: #c2cca0;
		stroke-width: @stroke-width;
	}
</style>
