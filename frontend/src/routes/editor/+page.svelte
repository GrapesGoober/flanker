<script lang="ts">
	import { onMount } from 'svelte';
	import { GetTerrainData, GetRifleSquadsData, type TerrainFeatureData, type Vec2 } from '$lib';
	import TerrainFeature from '$lib/terrain-feature.svelte';
	import SvgMap from '$lib/svg-map.svelte';

	let marker: Vec2 | null = $state(null);
	let terrainData: TerrainFeatureData[] = $state([]);

	onMount(async () => {
		terrainData = await GetTerrainData();
	});

	function AddMarker(event: MouseEvent, worldPos: Vec2) {
		marker = worldPos;
	}
</script>

<!-- I'm prototying behaviours at the moment, so proper structure comes later -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#snippet mapMarkup()}
	{#each terrainData as terrainFeatureData}
		<TerrainFeature featureData={terrainFeatureData} />
	{/each}

	{#if marker}
		<g>
			<circle cx={marker.x} cy={marker.y} r="10" fill="red" />
		</g>
	{/if}
{/snippet}

<SvgMap onclick={AddMarker} body={mapMarkup} />
