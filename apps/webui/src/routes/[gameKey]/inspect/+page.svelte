<script lang="ts">
	/*
	Logs page Svelte component
	Displays action logs, terrain, and unit state for replay and analysis.
	Handles log navigation and map rendering.
	*/
	import { page } from '$app/state';
	import { GetMapData, type MapViewState } from '$lib/api';
	import { SvgMap, TerrainLayer } from '$lib/components';
	import { loadGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';

	let mapData: MapViewState = $state({
		terrains: [],
		boundary: []
	});

	/* Loads terrain and log data on mount. */
	onMount(async () => {
		const gameKey: string = page.params['gameKey'] as string;
		const gameStateJson = loadGameLocal(gameKey);
		mapData = await GetMapData(gameStateJson);
	});
</script>

{#snippet mapSvgSnippet()}
	<TerrainLayer {mapData} />
{/snippet}

<div>
	<SvgMap svgSnippet={mapSvgSnippet} />
</div>
