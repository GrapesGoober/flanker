<script lang="ts">
	import { page } from '$app/state';
	import {
		GetLogs,
		GetMapData,
		type ActionLogModel,
		type MapViewStateModel
	} from '$lib/api';
	import { SvgMap, TerrainLayer } from '$lib/components';
	import { loadGameLocal } from '$lib/scenes-storage';
	import { onMount } from 'svelte';
	import LogViewLayer from './log-view-layer.svelte';

	let logData: ActionLogModel[] = $state([]);
	let index: number = $state(0);
	let mapData: MapViewStateModel = $state({
		terrains: [],
		boundary: []
	});
	let action: ActionLogModel | null = $derived(logData[index] ?? null);

	/* Loads terrain and log data on mount. */
	onMount(async () => {
		const gameKey: string = page.params['gameKey'] as string;
		const gameStateJson = await loadGameLocal(gameKey);
		mapData = await GetMapData(gameStateJson);
		logData = await GetLogs(gameStateJson);
	});
</script>

<!-- Map and log view layers for current log index -->
{#snippet mapSvgSnippet()}
	<TerrainLayer {mapData} />
	<LogViewLayer {logData} {index}></LogViewLayer>
{/snippet}
<!-- Log index input for navigation -->
index = <input type="number" class="number-input" bind:value={index} />

<!-- Map SVG rendering -->
<div class="resizable-map">
	<SvgMap svgSnippet={mapSvgSnippet} width="100%" height="100%" />
</div>

<!-- Display current action log details -->
{#if action}
	<div class="action-details">
		<pre><code>{JSON.stringify(action, null, 2)}</code></pre>
	</div>
{/if}

<style>
	.resizable-map {
		height: 70vh;
		min-height: 12rem;
		resize: vertical;
		overflow: hidden;
	}

	.action-details {
		height: 30vh;
		resize: vertical;
		overflow-y: scroll;
		background: #f5f5f5;
	}
</style>
